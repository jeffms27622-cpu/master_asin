import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. KONFIGURASI PRIBADI PAK ASIN
# ==========================================
MASTER_PASSWORD = st.secrets["ADMIN_PASSWORD"]
COMPANY_NAME = "PT. THEA THEO STATIONARY"

st.set_page_config(page_title="MY STRATEGY - Pak Asin", layout="wide")

def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open("Antrean Penawaran TTS")
    except:
        return None

# --- UI UTAMA ---
st.title("📓 My Strategic Notes")
st.subheader(f"Database Riset Gerilya - {COMPANY_NAME}")

pwd = st.sidebar.text_input("Akses Masuk:", type="password")

if pwd == MASTER_PASSWORD:
    wb = connect_gsheet()
    if wb:
        # Tampilan Langsung: Form Riset
        st.header("🎯 Input Target Customer Baru")
        
        with st.form("form_riset"):
            col1, col2 = st.columns(2)
            with col1:
                nama_pt = st.text_input("Nama Perusahaan (Target)")
                link_maps = st.text_area("Alamat / Link Google Maps", placeholder="Tempel alamat atau link maps")
            
            with col2:
                # Dropdown Barang Umpan agar tidak perlu ngetik ulang
                barang_umpan = st.selectbox("Barang Umpan:", 
                                           ["Lakban", "Stempel Kilat", "Kertas Foto", "Baterai", "Paper Clip", "Plastik Packing", "Lainnya..."])
                if barang_umpan == "Lainnya...":
                    barang_umpan = st.text_input("Sebutkan barang lain:")
                
                status_awal = st.selectbox("Status Saat Ini:", ["Baru Ketemu", "Sudah Dihubungi", "Kirim Sampel", "Deal / Goal"])
                catatan_pribadi = st.text_input("Catatan Strategi", placeholder="Misal: PIC-nya galak tapi butuh stempel")
            
            submit = st.form_submit_button("Simpan ke Buku Rahasia")
            
            if submit:
                try:
                    target_sheet = wb.worksheet("Riset_Pribadi_Asin")
                except:
                    target_sheet = wb.add_worksheet(title="Riset_Pribadi_Asin", rows="1000", cols="10")
                    target_sheet.append_row(["Tanggal", "Perusahaan", "Link Maps", "Barang Umpan", "Status", "Catatan"])
                
                target_sheet.append_row([
                    datetime.now().strftime("%d/%m/%Y"),
                    nama_pt, link_maps, barang_umpan, status_awal, catatan_pribadi
                ])
                st.success(f"Data {nama_pt} sudah tersimpan!")
                st.rerun() # Refresh biar muncul di tabel bawah

        st.divider()

        # --- DATABASE & PENCARIAN ---
        try:
            data_target = wb.worksheet("Riset_Pribadi_Asin").get_all_values()
            if len(data_target) > 1:
                df_target = pd.DataFrame(data_target[1:], columns=data_target[0])
                
                st.subheader("📁 Daftar Riset & Progress")
                
                # Fitur Search
                cari = st.text_input("🔍 Cari PT atau Lokasi (Contoh: Modernland):")
                if cari:
                    df_target = df_target[df_target.apply(lambda row: row.astype(str).str.contains(cari, case=False).any(), axis=1)]

                # Menampilkan Tabel dengan Kolom Link yang bisa diklik
                # Kita urutkan dari yang terbaru (paling atas)
                st.data_editor(
                    df_target.iloc[::-1], 
                    column_config={
                        "Link Maps": st.column_config.LinkColumn("Buka di Maps"),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Baru Ketemu", "Sudah Dihubungi", "Kirim Sampel", "Deal / Goal"])
                    },
                    use_container_width=True,
                    disabled=["Tanggal", "Perusahaan"] # Biar tidak sengaja teredit
                )
                
                st.caption("Tips: Bapak bisa langsung mengubah 'Status' di tabel atas dan data akan tersimpan (jika menggunakan data_editor).")
        except:
            st.info("Belum ada data riset.")

else:
    if pwd != "":
        st.error("Password Salah.")
