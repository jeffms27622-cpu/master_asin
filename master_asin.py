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
st.subheader(f"Database Riset Mandiri - {COMPANY_NAME}")

pwd = st.sidebar.text_input("Akses Masuk:", type="password")

if pwd == MASTER_PASSWORD:
    wb = connect_gsheet()
    if wb:
        # Tampilan Langsung: Form Riset
        st.header("🎯 Input Calon Customer Baru")
        
        with st.form("form_riset"):
            col1, col2 = st.columns(2)
            with col1:
                nama_pt = st.text_input("Nama Perusahaan (Target)")
                link_maps = st.text_area("Alamat / Link Google Maps", placeholder="Tempel alamat atau link maps hasil riset")
            
            with col2:
                barang_umpan = st.text_input("Barang Umpan (Contoh: Lakban, Stempel, Klip)")
                catatan_pribadi = st.text_input("Catatan Strategi", placeholder="Misal: Barang ini mereka butuh banyak")
            
            submit = st.form_submit_button("Simpan ke Database")
            
            if submit:
                try:
                    # Memakai sheet khusus riset pribadi
                    target_sheet = wb.worksheet("Riset_Pribadi_Asin")
                except:
                    target_sheet = wb.add_worksheet(title="Riset_Pribadi_Asin", rows="1000", cols="10")
                    target_sheet.append_row(["Tanggal", "Perusahaan", "Link Maps", "Barang Umpan", "Catatan"])
                
                target_sheet.append_row([
                    datetime.now().strftime("%d/%m/%Y"),
                    nama_pt, link_maps, barang_umpan, catatan_pribadi
                ])
                st.success(f"Data {nama_pt} sudah tersimpan di buku rahasia Bapak.")

        st.divider()

        # Tampilkan Database Riset
        try:
            data_target = wb.worksheet("Riset_Pribadi_Asin").get_all_values()
            if len(data_target) > 1:
                st.subheader("📁 Daftar Riset Saya")
                df_target = pd.DataFrame(data_target[1:], columns=data_target[0])
                # Menampilkan dari yang terbaru di atas
                st.dataframe(df_target.iloc[::-1], use_container_width=True)
        except:
            st.info("Belum ada data riset yang tersimpan.")

else:
    if pwd != "":
        st.error("Password Salah.")
