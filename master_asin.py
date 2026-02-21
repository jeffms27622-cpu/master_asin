import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. KONFIGURASI
# ==========================================
MASTER_PASSWORD = st.secrets["ADMIN_PASSWORD"] # Password Bapak
ADMIN_ENTRY_PWD = "ike"           # Password buat Admin (Bisa Bapak ganti)
COMPANY_NAME = "PT. THEA THEO STATIONARY"

st.set_page_config(page_title="STRATEGY SYSTEM - TTS", layout="wide")

def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open("Antrean Penawaran TTS")
    except:
        return None

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("🔑 Login System")
access_type = st.sidebar.radio("Masuk Sebagai:", ["Admin (Setor Data)", "Master (Pak Asin)"])
pwd = st.sidebar.text_input("Password:", type="password")

wb = connect_gsheet()

if wb:
    # ==========================================
    # HALAMAN ADMIN: HANYA BISA INPUT
    # ==========================================
    if access_type == "Admin (Setor Data)" and pwd == ADMIN_ENTRY_PWD:
        st.header("📥 Form Setoran Data Calon Customer")
        st.info("Silakan masukkan data hasil riset Google Maps di bawah ini.")
        
        with st.form("form_admin"):
            nama_pt = st.text_input("Nama Perusahaan")
            link_maps = st.text_area("Link Google Maps / Alamat")
            submit_admin = st.form_submit_button("Setor ke Master")
            
            if submit_admin:
                if nama_pt and link_maps:
                    try:
                        sheet = wb.worksheet("Riset_Pribadi_Asin")
                    except:
                        sheet = wb.add_worksheet(title="Riset_Pribadi_Asin", rows="1000", cols="10")
                        sheet.append_row(["Tanggal", "Perusahaan", "Link Maps", "Barang Umpan", "Status", "Catatan"])
                    
                    # Admin hanya mengisi 3 kolom pertama, sisanya kosong/default
                    sheet.append_row([
                        datetime.now().strftime("%d/%m/%Y"),
                        nama_pt, link_maps, "-", "Menunggu Strategi", "-"
                    ])
                    st.success("✅ Data berhasil disetor ke Pak Asin!")
                else:
                    st.error("Nama PT dan Maps wajib diisi!")

    # ==========================================
    # HALAMAN MASTER: KENDALI PENUH PAK ASIN
    # ==========================================
    elif access_type == "Master (Pak Asin)" and pwd == MASTER_PASSWORD:
        st.header("🛡️ Strategic Master Dashboard")
        
        try:
            target_sheet = wb.worksheet("Riset_Pribadi_Asin")
            data_all = target_sheet.get_all_values()
            
            if len(data_all) > 1:
                df_all = pd.DataFrame(data_all[1:], columns=data_all[0])
                
                # --- FITUR SEARCH ---
                cari = st.text_input("🔍 Cari PT atau Lokasi:")
                df_tampil = df_all.copy()
                if cari:
                    mask = df_tampil.apply(lambda row: row.astype(str).str.contains(cari, case=False).any(), axis=1)
                    df_tampil = df_tampil[mask]

                st.subheader("📁 Database Riset & Penentuan Strategi")
                
                # Pak Asin bisa edit: Barang Umpan, Status, dan Catatan
                # Tapi Nama PT dan Maps di-lock (disabled) agar tidak teracak
                edited_df = st.data_editor(
                    df_tampil.iloc[::-1], # Yang terbaru di atas
                    column_config={
                        "Link Maps": st.column_config.LinkColumn("Maps"),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Menunggu Strategi", "Siap Eksekusi", "Sudah Dihubungi", "Kirim Sampel", "Deal / Goal"]),
                        "Barang Umpan": st.column_config.TextColumn("Barang Umpan"),
                        "Catatan": st.column_config.TextColumn("Catatan Strategi")
                    },
                    use_container_width=True,
                    disabled=["Tanggal", "Perusahaan", "Link Maps"],
                    key="editor_master"
                )

                # Tombol Simpan Perubahan
                if st.button("💾 Simpan Perubahan Strategi"):
                    for index, row in edited_df.iterrows():
                        # Cari baris asli di Google Sheet berdasarkan Nama PT
                        match_idx = df_all[df_all['Perusahaan'] == row['Perusahaan']].index[0] + 2
                        # Update kolom 4 (Umpan), 5 (Status), 6 (Catatan)
                        target_sheet.update_cell(match_idx, 4, row['Barang Umpan'])
                        target_sheet.update_cell(match_idx, 5, row['Status'])
                        target_sheet.update_cell(match_idx, 6, row['Catatan'])
                    
                    st.toast("Strategi Berhasil Disimpan!", icon="🚀")
                    st.rerun()
            else:
                st.info("Belum ada setoran data dari Admin.")
        except Exception as e:
            st.error(f"Error: {e}")

    else:
        if pwd != "":
            st.warning("Password salah atau akses tidak diizinkan.")
