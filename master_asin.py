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
        
        with st.form("form_riset", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama_pt = st.text_input("Nama Perusahaan (Target)")
                link_maps = st.text_area("Alamat / Link Google Maps", placeholder="Tempel alamat atau link maps")
            
            with col2:
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
                st.rerun()

        st.divider()

        # --- DATABASE & PENCARIAN DENGAN AUTO-SAVE ---
        try:
            target_sheet = wb.worksheet("Riset_Pribadi_Asin")
            data_target = target_sheet.get_all_values()
            
            if len(data_target) > 1:
                df_all = pd.DataFrame(data_target[1:], columns=data_target[0])
                
                st.subheader("📁 Daftar Riset & Progress")
                
                # Fitur Search
                cari = st.text_input("🔍 Cari PT atau Lokasi:")
                df_tampil = df_all.copy()
                if cari:
                    df_tampil = df_tampil[df_tampil.apply(lambda row: row.astype(str).str.contains(cari, case=False).any(), axis=1)]

                # Gunakan data_editor untuk mengubah status
                edited_df = st.data_editor(
                    df_tampil, 
                    column_config={
                        "Link Maps": st.column_config.LinkColumn("Buka di Maps"),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Baru Ketemu", "Sudah Dihubungi", "Kirim Sampel", "Deal / Goal"])
                    },
                    use_container_width=True,
                    disabled=["Tanggal", "Perusahaan", "Link Maps", "Barang Umpan", "Catatan"],
                    key="editor_strategi"
                )

                # Logika Simpan Otomatis jika ada perubahan
                if not edited_df.equals(df_tampil):
                    # Cari baris mana yang berubah
                    for index, row in edited_df.iterrows():
                        # Ambil posisi baris asli di Google Sheet (index + 2 karena header dan mulai dari 1)
                        # Kita cari berdasarkan Nama Perusahaan agar akurat
                        original_row_idx = df_all[df_all['
