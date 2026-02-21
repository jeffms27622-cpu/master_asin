import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import plotly.express as px # Untuk grafik performa

# ==========================================
# 1. KONFIGURASI KHUSUS PAK ASIN
# ==========================================
MASTER_PASSWORD = st.secrets["ADMIN_PASSWORD"] # Pakai password admin yang sama
COMPANY_NAME = "PT. THEA THEO STATIONARY"

st.set_page_config(page_title="COMMAND CENTER - Pak Asin", layout="wide")

# --- KONEKSI GOOGLE SERVICES ---
def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        # Pastikan Bapak punya Sheet bernama 'Prospek' di file yang sama
        return client.open("Antrean Penawaran TTS")
    except:
        st.error("Gagal koneksi ke database.")
        return None

# --- UI UTAMA ---
st.title("🛡️ TTS Strategic Command Center")
st.subheader("Hanya untuk Pak Asin")

pwd = st.sidebar.text_input("Master Key:", type="password")

if pwd == MASTER_PASSWORD:
    wb = connect_gsheet()
    if wb:
        menu = st.sidebar.radio("Navigasi Strategis:", 
                                ["📊 Pantau Performa Marketing", 
                                 "🎯 Manajemen Prospek (Google Search)", 
                                 "🕵️ Intelijen Harga Kompetitor"])

        # --- MENU 1: PANTAU PERFORMA ---
        if menu == "📊 Pantau Performa Marketing":
            st.header("Ringkasan Aktivitas Tim")
            sheet_main = wb.sheet1
            data = sheet_main.get_all_values()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                
                # Statistik Cepat
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Penawaran", len(df))
                col2.metric("Proses Pending", len(df[df['Status'] == 'Pending']))
                col3.metric("Sales Aktif", df['Sales'].nunique())

                st.divider()
                st.subheader("Distribusi Kerja Marketing")
                fig = px.pie(df, names='Sales', title='Jumlah Penawaran per Sales')
                st.plotly_chart(fig)
                
                st.subheader("Log Transaksi Terbaru")
                st.dataframe(df.tail(10), use_container_width=True)

        # --- MENU 2: MANAJEMEN PROSPEK ---
        elif menu == "🎯 Manajemen Prospek (Google Search)":
            st.header("Input Target Customer Baru")
            st.info("Hasil riset Bapak di Google masukkan di sini sebelum dibagikan ke marketing.")
            
            with st.form("form_prospek"):
                nama_pt = st.text_input("Nama Perusahaan (Target)")
                bidang = st.selectbox("Bidang Usaha", ["Pabrik", "Sekolah", "Kantor/Ruko", "Lainnya"])
                alamat = st.text_area("Alamat / Link Google Maps")
                assign_to = st.selectbox("Tugaskan Ke:", ["Asin", "Alex", "Topan", "Artini"])
                submit = st.form_submit_button("Simpan & Tugaskan")
                
                if submit:
                    # Bapak bisa buat sheet baru bernama 'Target_Prospek' di file excel yang sama
                    try:
                        target_sheet = wb.worksheet("Target_Prospek")
                    except:
                        # Jika belum ada, buat otomatis (untuk pertama kali)
                        target_sheet = wb.add_worksheet(title="Target_Prospek", rows="100", cols="10")
                        target_sheet.append_row(["Tanggal", "Perusahaan", "Bidang", "Alamat", "Sales", "Status"])
                    
                    target_sheet.append_row([
                        datetime.now().strftime("%Y-%m-%d"),
                        nama_pt, bidang, alamat, assign_to, "Belum Dihubungi"
                    ])
                    st.success(f"Berhasil! {nama_pt} ditugaskan ke {assign_to}.")

        # --- MENU 3: INTELIJEN HARGA ---
        elif menu == "🕵️ Intelijen Harga Kompetitor":
            st.header("Catatan Harga Pasar")
            st.write("Gunakan untuk membandingkan harga TTS dengan kompetitor agar 'umpan' Bapak tepat sasaran.")
            
            # Form input simpel untuk database pribadi Bapak
            item = st.text_input("Nama Barang")
            h_tts = st.number_input("Harga Modal TTS", min_value=0)
            h_pasar = st.number_input("Harga Kompetitor (Hasil Intel)", min_value=0)
            
            if h_pasar > 0:
                selisih = h_pasar - h_tts
                st.warning(f"Potensi Keuntungan/Margin: Rp {selisih:,.0f}")
                if selisih > 0:
                    st.success("Kesimpulan: Harga kita kompetitif! Bisa jadi 'Barang Pintu Masuk'.")
                else:
                    st.error("Kesimpulan: Harga kita kalah. Cari supplier lain atau jangan jadikan umpan.")

else:
    if pwd != "":
        st.error("Akses Ditolak. Key Salah.")