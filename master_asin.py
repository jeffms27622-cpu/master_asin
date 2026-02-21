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
        return None

def buat_link_wa(nomor, nama_pt):
    if not nomor or nomor == "-" or nomor == "" or nomor == "None":
        return None
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
    try:
        target_sheet = wb.worksheet("Riset_Pribadi_Asin")
    except:
        target_sheet = wb.get_worksheet(0) 

    if access_type == "Admin (Setor Data)" and pwd == ADMIN_ENTRY_PWD:
        st.header("📥 Form Setoran Data (Admin)")
        with st.form("form_admin"):
            adm_nama = st.text_input("Nama Perusahaan / Customer")
            adm_wa = st.text_input("Nomor WA (Contoh: 0812345678)")
            adm_maps = st.text_area("Link Google Maps / Alamat")
            submit_admin = st.form_submit_button("Setor ke Master")
            
            if submit_admin:
                if adm_nama:
                    target_sheet.append_row([
                        datetime.now().strftime("%d/%m/%Y"), 
                        adm_nama, adm_wa if adm_wa else "-", adm_maps if adm_maps else "-",
                        "-", "Menunggu Strategi", "-"
                    ])
                    st.success(f"✅ Data {adm_nama} berhasil disetor!")
                else:
                    st.error("Nama Perusahaan wajib diisi!")

    elif access_type == "Master (Pak Asin)" and pwd == MASTER_PASSWORD:
        st.header("🛡️ Strategic Master Dashboard")
        
        with st.expander("➕ Input Riset Mandiri"):
            with st.form("form_master_input"):
                c1, c2 = st.columns(2)
                with c1:
                    m_pt = st.text_input("Nama Perusahaan")
                    m_wa = st.text_input("Nomor WA")
                    m_maps = st.text_area("Link Maps")
                with c2:
                    m_umpan = st.text_input("Barang Umpan")
                    m_catatan = st.text_input("Catatan Strategi")
                submit_master = st.form_submit_button("Simpan Riset Master")
                if submit_master and m_pt:
                    target_sheet.append_row([datetime.now().strftime("%d/%m/%Y"), m_pt, m_wa, m_maps, m_umpan, "Siap Eksekusi", m_catatan])
                    st.success("Berhasil simpan!")
                    st.rerun()

        st.divider()

        try:
            data_all = target_sheet.get_all_values()
            if len(data_all) > 0:
                # FIX: Menangani kolom kosong/duplikat
                headers = []
                for i, val in enumerate(data_all[0]):
                    if val.strip() == "":
                        headers.append(f"Kolom_{i}")
                    else:
                        headers.append(val)
                
                df_all = pd.DataFrame(data_all[1:], columns=headers)
                
                # Tambahkan Chat WA
                df_all['Chat WA'] = df_all.apply(lambda x: buat_link_wa(x[df_all.columns[2]], x[df_all.columns[1]]), axis=1)

                cari = st.text_input("🔍 Cari PT atau Lokasi:")
                df_tampil = df_all.copy()
                if cari:
                    df_tampil = df_tampil[df_tampil.apply(lambda row: row.astype(str).str.contains(cari, case=False).any(), axis=1)]

                edited_df = st.data_editor(
                    df_tampil.iloc[::-1],
                    column_config={
                        "Chat WA": st.column_config.LinkColumn("Action WA", display_text="Chat Sekarang 🟢"),
                        df_all.columns[3]: st.column_config.LinkColumn("Maps"),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Menunggu Strategi", "Siap Eksekusi", "Sudah Dihubungi", "Kirim Sampel", "Deal / Goal"]),
                    },
                    use_container_width=True,
                    disabled=[df_all.columns[0], "Chat WA"],
                    key="editor_master"
                )

                if st.button("💾 Simpan Perubahan Tabel"):
                    with st.spinner("Menyimpan..."):
                        for index, row in edited_df.iterrows():
                            try:
                                match_idx = df_all[df_all[df_all.columns[1]] == row[df_all.columns[1]]].index[0] + 2
                                for i in range(2, 7): # Update kolom 3 sampai 7
                                    target_sheet.update_cell(match_idx, i+1, str(row[df_all.columns[i]]))
                            except:
                                continue
                    st.toast("Data Diperbarui!", icon="🚀")
                    st.rerun()
            else:
                st.info("Database kosong.")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
    else:
        if pwd != "": st.error("Password Salah!")
else:
    st.error("Gagal terhubung ke Google Sheets.")
