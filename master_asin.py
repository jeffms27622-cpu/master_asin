import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import urllib.parse

# ==========================================
# 1. KONFIGURASI
# ==========================================
MASTER_PASSWORD = st.secrets["ADMIN_PASSWORD"] 
ADMIN_ENTRY_PWD = "ike"           
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

# --- FUNGSI WA LINK GENERATOR ---
def buat_link_wa(nomor, nama_pt):
    if not nomor or nomor == "-" or nomor == "":
        return None
    # Bersihkan nomor dari karakter non-angka
    nomor_bersih = ''.join(filter(str.isdigit, str(nomor)))
    if nomor_bersih.startswith('0'):
        nomor_bersih = '62' + nomor_bersih[1:]
    
    pesan = f"Halo Admin {nama_pt}, kami dari PT. THEA THEO STATIONARY (TTS) ingin menindaklanjuti..."
    pesan_encoded = urllib.parse.quote(pesan)
    return f"https://wa.me/{nomor_bersih}?text={pesan_encoded}"

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("🔑 Login System")
access_type = st.sidebar.radio("Masuk Sebagai:", ["Master (Pak Asin)", "Admin (Setor Data)"])
pwd = st.sidebar.text_input("Password:", type="password")

wb = connect_gsheet()

if wb:
    # ==========================================
    # HALAMAN ADMIN: HANYA BISA INPUT DATA MENTAH
    # ==========================================
    if access_type == "Admin (Setor Data)" and pwd == ADMIN_ENTRY_PWD:
        st.header("📥 Form Setoran Admin")
        with st.form("form_admin"):
            nama_pt = st.text_input("Nama Perusahaan")
            no_wa = st.text_input("Nomor WhatsApp (Contoh: 0812xxx)")
            link_maps = st.text_area("Link Google Maps / Alamat")
            submit_admin = st.form_submit_button("Setor ke Master")
            if submit_admin and nama_pt:
                try:
                    sheet = wb.worksheet("Riset_Pribadi_Asin")
                except:
                    sheet = wb.add_worksheet(title="Riset_Pribadi_Asin", rows="1000", cols="10")
                    sheet.append_row(["Tanggal", "Perusahaan", "WhatsApp", "Link Maps", "Barang Umpan", "Status", "Catatan"])
                
                sheet.append_row([
                    datetime.now().strftime("%d/%m/%Y"), 
                    nama_pt, no_wa if no_wa else "-", link_maps, "-", "Menunggu Strategi", "-"
                ])
                st.success(f"✅ Data {nama_pt} berhasil disetor!")

    # ==========================================
    # HALAMAN MASTER: DASHBOARD DENGAN TOMBOL WA
    # ==========================================
    elif access_type == "Master (Pak Asin)" and pwd == MASTER_PASSWORD:
        st.header("🛡️ Strategic Master Dashboard")
        
        with st.expander("➕ Input Riset Mandiri (Tanpa Admin)"):
            with st.form("form_master_input"):
                c1, c2 = st.columns(2)
                with c1:
                    m_pt = st.text_input("Nama Perusahaan")
                    m_wa = st.text_input("Nomor WhatsApp")
                    m_maps = st.text_area("Link Maps")
                with c2:
                    m_umpan = st.text_input("Barang Umpan")
                    m_catatan = st.text_input("Catatan Rahasia")
                
                if st.form_submit_button("Simpan Riset Saya"):
                    sheet = wb.worksheet("Riset_Pribadi_Asin")
                    sheet.append_row([datetime.now().strftime("%d/%m/%Y"), m_pt, m_wa, m_maps, m_umpan, "Siap Eksekusi", m_catatan])
                    st.success("Berhasil simpan!")
                    st.rerun()

        st.divider()

        try:
            target_sheet = wb.worksheet("Riset_Pribadi_Asin")
            data_all = target_sheet.get_all_values()
            if len(data_all) > 1:
                df_all = pd.DataFrame(data_all[1:], columns=data_all[0])
                
                # Buat Link WA otomatis
                df_all['Chat WA'] = df_all.apply(lambda x: buat_link_wa(x['WhatsApp'], x['Perusahaan']), axis=1)

                st.subheader("📁 Database & Fast Response")
                cari = st.text_input("🔍 Cari PT atau Lokasi:")
                df_tampil = df_all.copy()
                
                if cari:
                    # Perbaikan filter pencarian agar tidak error
                    df_tampil = df_tampil[df_tampil.apply(lambda row: row.astype(str).str.contains(cari, case=False).any(), axis=1)]

                edited_df = st.data_editor(
                    df_tampil.iloc[::-1],
                    column_config={
                        "Chat WA": st.column_config.LinkColumn("Hubungi WA", display_text="Kirim Pesan 🟢"),
                        "Link Maps": st.column_config.LinkColumn("Maps"),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Menunggu Strategi", "Siap Eksekusi", "Sudah Dihubungi", "Kirim Sampel", "Deal / Goal"]),
                    },
                    use_container_width=True,
                    disabled=["Tanggal", "Chat WA"], 
                    key="editor_master"
                )

                if st.button("💾 Simpan Semua Perubahan"):
                    for index, row in edited_df.iterrows():
                        match_idx = df_all[df_all['Perusahaan'] == row['Perusahaan']].index[0] + 2
                        target_sheet.update_cell(match_idx, 2, row['Perusahaan'])
                        target_sheet.update_cell(match_idx, 3, row['WhatsApp'])
                        target_sheet.update_cell(match_idx, 4, row['Link Maps'])
                        target_sheet.update_cell(match_idx, 5, row['Barang Umpan'])
                        target_sheet.update_cell(match_idx, 6, row['Status'])
                        target_sheet.update_cell(match_idx, 7, row['Catatan'])
                    st.toast("Data Diperbarui!", icon="🚀")
                    st.rerun()
            else:
                st.info("Belum ada data di Google Sheets.")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat menarik data: {e}")
    else:
        if pwd != "":
            st.error("Password salah. Silakan coba lagi.")

