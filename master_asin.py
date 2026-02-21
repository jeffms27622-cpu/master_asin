import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. KONFIGURASI
# ==========================================
MASTER_PASSWORD = st.secrets["ADMIN_PASSWORD"]
COMPANY_NAME = "PT. THEA THEO STATIONARY"

st.set_page_config(page_title="STRATEGY CENTER - Pak Asin", layout="wide")

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
st.title("🛡️ TTS Strategic Command Center")
st.subheader(f"Pengendali Penjualan - {COMPANY_NAME}")

pwd = st.sidebar.text_input("Master Key:", type="password")

if pwd == MASTER_PASSWORD:
    wb = connect_gsheet()
    if wb:
        menu = st.sidebar.radio("Navigasi:", 
                                ["📊 Pantau Performa Marketing", 
                                 "🎯 Manajemen Prospek & Barang Umpan"])

        # --- MENU 1: PANTAU PERFORMA ---
        if menu == "📊 Pantau Performa Marketing":
            st.header("Ringkasan Aktivitas Tim")
            sheet_main = wb.sheet1
            data = sheet_main.get_all_values()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                st.metric("Total Penawaran Terbit", len(df))
                st.subheader("Data Penawaran Terakhir")
                st.dataframe(df.tail(20), use_container_width=True)
            else:
                st.info("Belum ada data penawaran masuk dari marketing.")

        # --- MENU 2: MANAJEMEN PROSPEK ---
        elif menu == "🎯 Manajemen Prospek & Barang Umpan":
            st.header("Target Customer & Strategi Pintu Masuk")
            st.markdown("---")
            
            with st.form("form_prospek"):
                col1, col2 = st.columns(2)
                with col1:
                    nama_pt = st.text_input("Nama Perusahaan (Target)")
                    assign_to = st.selectbox("Tugaskan Ke:", ["Alex", "Topan", "Artini"])
                with col2:
                    # FITUR NO. 3: BARANG RECEH/UMPAN
                    barang_umpan = st.text_input("Barang Umpan (Misal: Lakban, Stempel, Klip)", help="Barang kecil untuk pembuka pintu meeting")
                    catatan_strategi = st.text_input("Pesan Khusus untuk Marketing", placeholder="Misal: Tawarkan sampel gratis dulu")
                
                submit = st.form_submit_button("Kirim Tugas ke Marketing")
                
                if submit:
                    try:
                        target_sheet = wb.worksheet("Target_Prospek")
                    except:
                        target_sheet = wb.add_worksheet(title="Target_Prospek", rows="500", cols="10")
                        target_sheet.append_row(["Tanggal", "Perusahaan", "Sales", "Barang Umpan", "Pesan Strategi", "Status"])
                    
                    target_sheet.append_row([
                        datetime.now().strftime("%d/%m/%Y"),
                        nama_pt, assign_to, barang_umpan, catatan_strategi, "Belum Dihubungi"
                    ])
                    st.success(f"Strategi dicatat! {nama_pt} akan ditembak dengan {barang_umpan} oleh {assign_to}.")

            # Tampilkan Daftar Tunggu Prospek
            try:
                data_target = wb.worksheet("Target_Prospek").get_all_values()
                if len(data_target) > 1:
                    st.subheader("Daftar Pantauan Prospek")
                    df_target = pd.DataFrame(data_target[1:], columns=data_target[0])
                    st.table(df_target.tail(10))
            except:
                pass

else:
    if pwd != "":
        st.error("Akses Ditolak.")
