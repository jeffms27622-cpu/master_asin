import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import urllib.parse

# ==========================================
# 1. KONFIGURASI & KONEKSI
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
    except Exception as e:
        st.error(f"Gagal koneksi ke Google Sheets: {e}")
        return None

# --- FUNGSI WA LINK GENERATOR ---
def buat_link_wa(nomor, nama_pt):
    if not nomor or nomor == "-" or nomor == "" or nomor == "None":
        return None
    # Bersihkan nomor dari karakter non-angka
    nomor_bersih = ''.join(filter(str.isdigit, str(nomor)))
    if nomor_bersih.startswith('0'):
        nomor_bersih = '62' + nomor_bersih[1:]
    elif nomor_bersih.startswith('8'):
        nomor_bersih = '62' + nomor_bersih
    
    pesan = f"Halo Admin {nama_pt}, kami dari PT. THEA THEO STATIONARY (TTS) ingin menindaklanjuti..."
    pesan_encoded = urllib.parse.quote(pesan)
    return f"https://wa.me/{nomor_bersih}?text={pesan_encoded}"

# --- SIDEBAR NAVIGASI ---
st.sidebar.title(f"🔑 {COMPANY_NAME}")
access_type = st.sidebar.radio("Masuk Sebagai:", ["Master (Pak Asin)", "Admin (Setor Data)"])
pwd = st.sidebar.text_input("Password:", type="password")

wb = connect_gsheet()

if wb:
    # Memilih Sheet. Jika 'Riset_Pribadi_Asin' tidak ada, pakai sheet pertama.
    try:
        target_sheet = wb.worksheet("Riset_Pribadi_Asin")
    except:
        target_sheet = wb.get_worksheet(0) 

    # ==========================================
    # HALAMAN ADMIN: HANYA BISA INPUT
    # ==========================================
    if access_type == "Admin (Setor Data)" and pwd == ADMIN_ENTRY_PWD:
        st.header("📥 Form Setoran Data (Admin)")
        st.info("Gunakan form ini untuk memasukkan data calon customer baru.")
        
        with st.form("form_admin"):
            nama_pt = st.text_input("Nama Perusahaan / Customer")
            no_wa = st.text_input("Nomor WA (Contoh: 0812345678)")
            link_maps = st.text_area("Link Google Maps / Alamat")
            submit_admin = st.form
