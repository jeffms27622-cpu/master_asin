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

def buat_link_wa(nomor, nama_pt):
    if not nomor or nomor in ["-", "", "None"]:
        return None
    nomor_bersih = ''.join(filter(str.isdigit, str(nomor)))
    if nomor_bersih.startswith('0'):
        nomor_bersih = '62' + nomor_bersih[1:]
    elif nomor_bersih.startswith('8'):
        nomor_bersih = '62' + nomor_bersih
    
    pesan = f"Halo Admin {nama_pt}, kami dari PT. THEA THEO STATIONARY (TTS)..."
    pesan_encoded = urllib.parse.quote(pesan)
    return f"https://wa.me/{nomor_bersih}?text={pesan_encoded}"

# --- LOGIN SYSTEM ---
st.sidebar.title(f"🔑 {COMPANY_NAME}")
access_type = st.sidebar.radio("Masuk Sebagai:", ["Master (Pak Asin)", "Admin (Setor Data)"])
pwd = st.sidebar.text_input("Password:", type="password")

wb = connect_gsheet()

if wb:
    try:
        target_sheet = wb.worksheet("Riset_Pribadi_Asin")
    except:
        target_sheet = wb.get_worksheet(0) 

    # --- HALAMAN ADMIN ---
    if access_type == "Admin (Setor Data)" and pwd == ADMIN_ENTRY_PWD:
        st.header("📥 Form Setoran Data (Admin)")
        with st.form("form_admin"):
            adm_nama = st.text_input("Nama Perusahaan")
            adm_wa = st.text_input("Nomor WA")
            adm_maps = st.text_area("Link Maps")
            if st.form_submit_button("Setor ke Master"):
                if adm_nama:
                    target_sheet.append_row([datetime.now().strftime("%d/%m/%Y"), adm_nama, adm_wa, adm_maps, "-", "Menunggu Strategi", "-"])
                    st.success("Berhasil disetor!")
                else:
                    st.error("Nama wajib diisi!")

    # --- HALAMAN MASTER ---
    elif access_type == "Master (Pak Asin)" and pwd == MASTER_PASSWORD:
        st.header("🛡️ Strategic Master Dashboard")
        
        with st.expander("➕ Input Riset Mandiri"):
            with st.form("form_master"):
                c1, c2 = st.columns(2)
                with c1:
                    m_pt = st.text_input("Nama Perusahaan")
                    m_wa = st.text_input("Nomor WA")
                    m_maps = st.text_area("Link Maps")
                with c2:
                    m_umpan = st.text_input("Barang Umpan")
                    m_catatan = st.text_input("Catatan Strategi")
                if st.form_submit_button("Simpan Master") and m_pt:
                    target_sheet.append_row([datetime.now().strftime("%d/%m/%Y"), m_pt, m_wa, m_maps, m_umpan, "Siap Eksekusi", m_catatan])
                    st.rerun()

        st.divider()

        # MANAJEMEN DATA
        raw_data = target_sheet.get_all_values()
        if len(raw_data) > 0:
            # Paksa Header supaya tidak loncat
            kolom_fixed = ["Tanggal", "Perusahaan", "WA", "Link Maps", "Barang Umpan", "Status", "Catatan"]
            df = pd.DataFrame(raw_data[1:], columns=kolom_fixed[:len(raw_data[0])])
            
            # Tambah kolom Chat WA di posisi paling akhir (hanya di tampilan)
            df['Chat_WA'] = df.apply(lambda x: buat_link_wa(x['WA'], x['Perusahaan']) if 'WA' in df.columns else None, axis=1)

            cari = st.text_input("🔍 Cari PT / Lokasi:")
            if cari:
                df = df[df.apply(lambda r: r.astype(str).str.contains(cari, case=False).any(), axis=1)]

            edited_df = st.data_editor(
                df.iloc[::-1],
                column_config={
                    "Chat_WA": st.column_config.LinkColumn("Action WA", display_text="Chat Sekarang 🟢"),
                    "Link Maps": st.column_config.LinkColumn("Maps"),
                    "Status": st.column_config.SelectboxColumn("Status", options=["Menunggu Strategi", "Siap Eksekusi", "Sudah Dihubungi", "Kirim Sampel", "Deal / Goal"]),
                },
                use_container_width=True,
                disabled=["Tanggal", "Chat_WA"],
                key="master_editor"
            )

            if st.button("💾 Simpan Perubahan"):
                with st.spinner("Menyimpan ke Google Sheets..."):
                    # Proses simpan balik ke baris yang tepat
                    for index, row in edited_df.iterrows():
                        # Cari baris asli (indeks di pandas + 2 untuk header gsheet)
                        # Kita gunakan nama PT sebagai kunci unik
                        try:
                            # Cari baris ke berapa PT ini berada di data asli
                            line_idx = raw_data[1:].index(list(raw_data[raw_data[1:].index(list(df.loc[index, kolom_fixed[:len(raw_data[0])]])) + 1])) + 2
                        except:
                            # Jika pusing dengan index, kita pakai cara aman: cocokkan nama PT
                            cells = target_sheet.find(row['Perusahaan'])
                            line_idx = cells.row
                        
                        # Update per kolom secara kaku agar tidak loncat
                        update_data = [
                            [row['WA'], row['Link Maps'], row['Barang Umpan'], row['Status'], row['Catatan']]
                        ]
                        # Update range kolom C sampai G (3 sampai 7)
                        target_sheet.update(f"C{line_idx}:G{line_idx}", update_data)
                st.success("Berhasil disimpan!")
                st.rerun()
    else:
        if pwd != "": st.error("Password Salah")
else:
    st.error("Koneksi GSheet Gagal")
