import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import urllib.parse
import io

# ==========================================
# KONFIGURASI
# ==========================================
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SHEET_NAME = "Antrean Penawaran TTS"
WORKSHEET_NAME = "Riset_Pribadi_Asin"

KOLOM = ["Tanggal", "Perusahaan", "Kategori", "WA", "Link Maps",
         "Barang Umpan", "Sumber", "Status", "Follow Up",
         "Histori", "Catatan"]

STATUS_OPTIONS = [
    "Menunggu Strategi",
    "Siap Eksekusi",
    "Sudah Dihubungi",
    "Kirim Sampel",
    "Negosiasi",
    "Deal / Goal",
    "Tidak Tertarik",
]

KATEGORI_OPTIONS = ["Sekolah", "Kantor Pemerintah", "Kantor Swasta",
                    "Toko / Reseller", "Instansi / Yayasan", "Lainnya"]

SUMBER_OPTIONS = ["Kunjungan Lapangan", "Referral", "Google Maps",
                  "Marketplace", "Media Sosial", "Lainnya"]

STATUS_COLOR = {
    "Menunggu Strategi": "#888780",
    "Siap Eksekusi":     "#378ADD",
    "Sudah Dihubungi":   "#BA7517",
    "Kirim Sampel":      "#7F77DD",
    "Negosiasi":         "#D85A30",
    "Deal / Goal":       "#1D9E75",
    "Tidak Tertarik":    "#E24B4A",
}

# ==========================================
# CSS KUSTOM
# ==========================================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Sora:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    #MainMenu, footer, header { visibility: hidden; }

    .tts-header {
        background: linear-gradient(135deg, #0a1628 0%, #112240 60%, #1a3a6b 100%);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid rgba(55, 138, 221, 0.25);
    }
    .tts-header h1 {
        font-family: 'Sora', sans-serif;
        font-size: 22px;
        font-weight: 600;
        color: #e8f4fd;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .tts-header p {
        font-size: 13px;
        color: #85b7eb;
        margin: 4px 0 0;
    }
    .tts-logo {
        font-family: 'Sora', sans-serif;
        font-size: 20px;
        font-weight: 600;
        color: #378ADD;
        background: rgba(55,138,221,0.12);
        width: 52px; height: 52px;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        border: 1px solid rgba(55,138,221,0.3);
    }

    .metric-row { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
    .metric-card {
        flex: 1; min-width: 110px;
        background: #fff;
        border: 1px solid #e8e8e8;
        border-radius: 12px;
        padding: 14px 16px;
    }
    .metric-card .label { font-size: 11px; color: #999; margin-bottom: 4px; }
    .metric-card .value { font-size: 24px; font-weight: 700; color: #0a1628; }
    .metric-card .sub { font-size: 11px; color: #bbb; margin-top: 2px; }

    .badge {
        display: inline-block;
        font-size: 11px; font-weight: 600;
        padding: 3px 10px; border-radius: 20px;
        letter-spacing: 0.02em;
    }

    .section-label {
        font-size: 11px; font-weight: 600; color: #999;
        text-transform: uppercase; letter-spacing: 0.06em;
        margin: 20px 0 10px;
    }

    [data-testid="stSidebar"] {
        background: #0a1628 !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div { color: #8892b0 !important; }

    .alert-box {
        background: #fff8e6; border: 1px solid #f0c040;
        border-radius: 10px; padding: 12px 16px;
        font-size: 13px; color: #7a5500; margin-bottom: 16px;
    }

    .histori-box {
        background: #f8f9fc; border-radius: 8px;
        padding: 10px 14px; font-size: 12px;
        color: #555; white-space: pre-wrap; line-height: 1.6;
        border: 1px solid #ececec; margin-top: 6px;
    }

    .wa-btn {
        display: inline-block;
        background: #1D9E75; color: #fff !important;
        font-size: 12px; font-weight: 600;
        padding: 5px 12px; border-radius: 8px;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# GOOGLE SHEETS HELPERS
# ==========================================
def get_creds():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)

@st.cache_resource(ttl=30)
def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        wb = client.open(SHEET_NAME)
        try:
            ws = wb.worksheet(WORKSHEET_NAME)
        except Exception:
            ws = wb.get_worksheet(0)
        return ws
    except Exception:
        return None

def load_data(ws):
    raw = ws.get_all_values()
    if len(raw) <= 1:
        return pd.DataFrame(columns=KOLOM), raw
    df = pd.DataFrame(raw[1:], columns=KOLOM[:len(raw[0])])
    for col in KOLOM:
        if col not in df.columns:
            df[col] = ""
    return df, raw

def simpan_semua(ws, df):
    """Tulis ulang seluruh sheet secara aman."""
    all_rows = [KOLOM]
    for _, row in df.iterrows():
        all_rows.append([str(row.get(k, "")) for k in KOLOM])
    ws.clear()
    ws.update("A1", all_rows)

def buat_link_wa(nomor, nama_pt):
    if not nomor or str(nomor).strip() in ["-", "", "None"]:
        return None
    n = ''.join(filter(str.isdigit, str(nomor)))
    if n.startswith('0'):
        n = '62' + n[1:]
    elif n.startswith('8'):
        n = '62' + n
    pesan = (f"Halo, perkenalkan kami dari {COMPANY_NAME}.\n"
             f"Kami ingin menawarkan produk alat tulis kantor & stationary "
             f"berkualitas untuk {nama_pt}.\n"
             f"Apakah ada waktu untuk berdiskusi lebih lanjut? 🙏")
    return f"https://wa.me/{n}?text={urllib.parse.quote(pesan)}"

# ==========================================
# KOMPONEN UI
# ==========================================
def render_header(role):
    st.markdown(f"""
    <div class="tts-header">
      <div>
        <h1>Strategy System — TTS</h1>
        <p>{COMPANY_NAME} &nbsp;·&nbsp; {role}</p>
      </div>
      <div class="tts-logo">TTS</div>
    </div>
    """, unsafe_allow_html=True)

def render_metrics(df):
    total      = len(df)
    deal       = len(df[df['Status'] == 'Deal / Goal'])
    eksekusi   = len(df[df['Status'] == 'Siap Eksekusi'])
    dihubungi  = len(df[df['Status'] == 'Sudah Dihubungi'])
    today_str  = date.today().strftime("%d/%m/%Y")
    fu_today   = len(df[df['Follow Up'] == today_str])
    pct        = round(deal / total * 100) if total > 0 else 0

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card">
        <div class="label">Total Prospek</div>
        <div class="value">{total}</div>
        <div class="sub">semua status</div>
      </div>
      <div class="metric-card">
        <div class="label">Deal / Goal</div>
        <div class="value" style="color:#1D9E75">{deal}</div>
        <div class="sub">{pct}% konversi</div>
      </div>
      <div class="metric-card">
        <div class="label">Siap Eksekusi</div>
        <div class="value" style="color:#378ADD">{eksekusi}</div>
        <div class="sub">antrian aktif</div>
      </div>
      <div class="metric-card">
        <div class="label">Sudah Dihubungi</div>
        <div class="value" style="color:#BA7517">{dihubungi}</div>
        <div class="sub">menunggu respons</div>
      </div>
      <div class="metric-card">
        <div class="label">Follow Up Hari Ini</div>
        <div class="value" style="color:#D85A30">{fu_today}</div>
        <div class="sub">{today_str}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_followup_alert(df):
    today_str = date.today().strftime("%d/%m/%Y")
    fu = df[df['Follow Up'] == today_str]
    if len(fu) > 0:
        names = ", ".join(fu['Perusahaan'].tolist()[:5])
        extra = f" +{len(fu)-5} lainnya" if len(fu) > 5 else ""
        st.markdown(f"""
        <div class="alert-box">
          ⏰ <b>Follow Up Hari Ini ({len(fu)} prospek):</b> {names}{extra}
        </div>
        """, unsafe_allow_html=True)

def badge_html(status):
    color = STATUS_COLOR.get(status, "#888")
    bg    = color + "22"
    return f'<span class="badge" style="background:{bg};color:{color};">{status}</span>'

# ==========================================
# HALAMAN MASTER
# ==========================================
def halaman_master(ws):
    render_header("Master Dashboard — Pak Asin")
    df, raw = load_data(ws)

    render_metrics(df)
    render_followup_alert(df)

    # ---- Form Input Baru ----
    with st.expander("➕ Tambah Prospek Baru", expanded=False):
        with st.form("form_master", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                m_pt       = st.text_input("Nama Perusahaan *")
                m_kategori = st.selectbox("Kategori", KATEGORI_OPTIONS)
                m_wa       = st.text_input("Nomor WA")
            with c2:
                m_maps   = st.text_input("Link Google Maps")
                m_umpan  = st.text_input("Barang Umpan")
                m_sumber = st.selectbox("Sumber Prospek", SUMBER_OPTIONS)
            with c3:
                m_status   = st.selectbox("Status Awal", STATUS_OPTIONS)
                m_followup = st.date_input("Jadwal Follow Up", value=None)
                m_catatan  = st.text_area("Catatan Strategi", height=82)

            if st.form_submit_button("💾 Simpan Prospek", use_container_width=True):
                if not m_pt.strip():
                    st.error("Nama perusahaan wajib diisi!")
                else:
                    fu_str = m_followup.strftime("%d/%m/%Y") if m_followup else ""
                    ws.append_row([
                        datetime.now().strftime("%d/%m/%Y"),
                        m_pt.strip(), m_kategori, m_wa, m_maps,
                        m_umpan, m_sumber, m_status, fu_str, "", m_catatan
                    ])
                    st.success(f"✅ Prospek '{m_pt}' berhasil disimpan!")
                    st.cache_resource.clear()
                    st.rerun()

    st.markdown('<p class="section-label">Daftar Prospek</p>', unsafe_allow_html=True)

    # ---- Filter & Sort ----
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    with col1:
        cari = st.text_input("Cari", placeholder="🔍 Cari nama / catatan...",
                             label_visibility="collapsed")
    with col2:
        filter_status = st.multiselect("Status", STATUS_OPTIONS,
                                       placeholder="Semua status",
                                       label_visibility="collapsed")
    with col3:
        filter_kat = st.multiselect("Kategori", KATEGORI_OPTIONS,
                                    placeholder="Semua kategori",
                                    label_visibility="collapsed")
    with col4:
        sort_by = st.selectbox("Urutkan", ["Terbaru", "Terlama", "Status", "Follow Up"],
                               label_visibility="collapsed")

    df_view = df.copy()
    if cari:
        mask = df_view.apply(
            lambda r: r.astype(str).str.contains(cari, case=False).any(), axis=1)
        df_view = df_view[mask]
    if filter_status:
        df_view = df_view[df_view['Status'].isin(filter_status)]
    if filter_kat:
        df_view = df_view[df_view['Kategori'].isin(filter_kat)]

    df_view = df_view.reset_index(drop=False)  # simpan index asli

    if sort_by == "Terbaru":
        df_view = df_view.iloc[::-1].reset_index(drop=True)
    elif sort_by == "Status":
        order = {s: i for i, s in enumerate(STATUS_OPTIONS)}
        df_view['_s'] = df_view['Status'].map(order)
        df_view = df_view.sort_values('_s').drop(columns='_s').reset_index(drop=True)
    elif sort_by == "Follow Up":
        df_view = df_view.sort_values('Follow Up').reset_index(drop=True)

    st.markdown(
        f"<p style='font-size:12px;color:#bbb;margin-bottom:8px;'>"
        f"{len(df_view)} prospek ditemukan</p>",
        unsafe_allow_html=True)

    today_str = date.today().strftime("%d/%m/%Y")

    for _, row in df_view.iterrows():
        orig_idx = row.get('index', _)
        wa_link  = buat_link_wa(row.get('WA', ''), row.get('Perusahaan', ''))
        wa_btn   = (f'<a href="{wa_link}" target="_blank" class="wa-btn">Chat WA 💬</a>'
                    if wa_link else "–")
        maps_link = row.get('Link Maps', '')
        maps_btn  = (f'<a href="{maps_link}" target="_blank" '
                     f'style="font-size:12px;color:#378ADD;">Buka Maps 📍</a>'
                     if maps_link else "–")
        fu = row.get('Follow Up', '')
        fu_disp = (f"<span style='color:#D85A30;font-weight:600;'>⏰ {fu} (HARI INI)</span>"
                   if fu == today_str else fu or "–")

        label = f"**{row['Perusahaan']}** — {row.get('Kategori','')}  {badge_html(row.get('Status',''))}"
        with st.expander(label, expanded=False):
            ec1, ec2, ec3 = st.columns([2, 2, 1.5])

            with ec1:
                st.markdown("**Info Prospek**")
                st.markdown(f"🏢 Kategori: **{row.get('Kategori','-')}**")
                st.markdown(f"📡 Sumber: {row.get('Sumber','-')}")
                st.markdown(f"📞 WA: {row.get('WA','-')}", unsafe_allow_html=True)
                st.markdown(wa_btn, unsafe_allow_html=True)
                st.markdown(maps_btn, unsafe_allow_html=True)
                st.markdown(f"🎯 Barang Umpan: **{row.get('Barang Umpan','-')}**")
                st.markdown(f"📅 Input: {row.get('Tanggal','-')}")

            with ec2:
                st.markdown("**Progress & Histori**")
                st.markdown(f"📌 Follow Up: ", unsafe_allow_html=True)
                st.markdown(fu_disp, unsafe_allow_html=True)
                st.markdown(f"📝 Catatan: {row.get('Catatan','-')}")
                histori = row.get('Histori', '')
                if histori:
                    st.markdown("**Riwayat Kontak:**")
                    st.markdown(
                        f'<div class="histori-box">{histori}</div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        "<span style='font-size:12px;color:#bbb;'>Belum ada histori.</span>",
                        unsafe_allow_html=True)

            with ec3:
                st.markdown("**Edit**")
                new_status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(row['Status'])
                          if row['Status'] in STATUS_OPTIONS else 0,
                    key=f"st_{orig_idx}")

                fu_val = None
                if row.get('Follow Up', ''):
                    try:
                        fu_val = datetime.strptime(row['Follow Up'], "%d/%m/%Y").date()
                    except Exception:
                        fu_val = None
                new_fu = st.date_input("Follow Up", value=fu_val,
                                       key=f"fu_{orig_idx}")
                new_cat = st.text_input("Catatan", value=row.get('Catatan', ''),
                                        key=f"ct_{orig_idx}")
                new_hist = st.text_input(
                    "+ Log baru",
                    placeholder="cth: sudah kirim sampel...",
                    key=f"ht_{orig_idx}")

                col_s, col_d = st.columns(2)
                with col_s:
                    if st.button("💾 Simpan", key=f"save_{orig_idx}",
                                 use_container_width=True):
                        df_full, raw2 = load_data(ws)
                        mask2 = ((df_full['Perusahaan'] == row['Perusahaan']) &
                                 (df_full['Tanggal']    == row['Tanggal']))
                        idxs = df_full[mask2].index.tolist()
                        if idxs:
                            t = idxs[0]
                            df_full.at[t, 'Status']   = new_status
                            df_full.at[t, 'Follow Up'] = (
                                new_fu.strftime("%d/%m/%Y") if new_fu else "")
                            df_full.at[t, 'Catatan']  = new_cat
                            if new_hist.strip():
                                tgl_now = datetime.now().strftime("%d/%m %H:%M")
                                old_h   = df_full.at[t, 'Histori']
                                df_full.at[t, 'Histori'] = (
                                    f"[{tgl_now}] {new_hist.strip()}\n{old_h}".strip())
                            simpan_semua(ws, df_full)
                            st.success("Tersimpan!")
                            st.cache_resource.clear()
                            st.rerun()
                with col_d:
                    if st.button("🗑️ Hapus", key=f"del_{orig_idx}",
                                 use_container_width=True, type="secondary"):
                        df_full, raw2 = load_data(ws)
                        mask2 = ((df_full['Perusahaan'] == row['Perusahaan']) &
                                 (df_full['Tanggal']    == row['Tanggal']))
                        df_full = df_full[~mask2].reset_index(drop=True)
                        simpan_semua(ws, df_full)
                        st.success("Dihapus!")
                        st.cache_resource.clear()
                        st.rerun()

    # ---- Export ----
    st.divider()
    st.markdown('<p class="section-label">Export Data</p>', unsafe_allow_html=True)
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine='openpyxl')
        st.download_button(
            "📥 Download Excel (Semua Data)", buf.getvalue(),
            file_name=f"TTS_Prospek_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with col_e2:
        buf2 = io.BytesIO()
        df_view.drop(columns=['index'], errors='ignore').to_excel(
            buf2, index=False, engine='openpyxl')
        st.download_button(
            "📥 Download Excel (Filter Aktif)", buf2.getvalue(),
            file_name=f"TTS_Filter_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

# ==========================================
# HALAMAN ADMIN
# ==========================================
def halaman_admin(ws):
    render_header("Form Setoran Data (Admin)")
    st.info("Isi data calon customer dan klik Setor. "
            "Data akan langsung masuk ke sistem Master untuk ditindaklanjuti.")

    with st.form("form_admin", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            adm_nama     = st.text_input("Nama Perusahaan *")
            adm_kategori = st.selectbox("Kategori", KATEGORI_OPTIONS)
            adm_wa       = st.text_input("Nomor WA")
        with c2:
            adm_maps    = st.text_input("Link Google Maps")
            adm_sumber  = st.selectbox("Sumber Prospek", SUMBER_OPTIONS)
            adm_catatan = st.text_area("Catatan Singkat", height=82)

        if st.form_submit_button("📤 Setor ke Master", use_container_width=True):
            if not adm_nama.strip():
                st.error("Nama perusahaan wajib diisi!")
            else:
                ws.append_row([
                    datetime.now().strftime("%d/%m/%Y"),
                    adm_nama.strip(), adm_kategori, adm_wa, adm_maps,
                    "", adm_sumber, "Menunggu Strategi",
                    "", "", adm_catatan
                ])
                st.success(f"✅ Data '{adm_nama}' berhasil disetor ke Master!")
                st.cache_resource.clear()

# ==========================================
# MAIN
# ==========================================
st.set_page_config(
    page_title="Strategy System — TTS",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_css()

# ---- Sidebar ----
with st.sidebar:
    st.markdown(f"""
    <div style='padding:20px 0 10px;'>
      <div style='font-family:Sora,sans-serif;font-size:20px;font-weight:700;
                  color:#378ADD;letter-spacing:-0.5px;margin-bottom:4px;'>TTS</div>
      <div style='font-size:11px;color:#4a5568;line-height:1.5;'>
        {COMPANY_NAME}<br>Strategy &amp; Prospek System
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown(
        "<div style='font-size:11px;color:#4a5568;margin-bottom:8px;'>"
        "MASUK SEBAGAI</div>",
        unsafe_allow_html=True)
    access_type = st.radio("", ["Master (Pak Asin)", "Admin (Setor Data)"],
                           label_visibility="collapsed")
    pwd = st.text_input("Password", type="password",
                        placeholder="Masukkan password...")
    st.divider()
    st.markdown(
        f"<div style='font-size:11px;color:#4a5568;line-height:1.8;'>"
        f"📅 {datetime.now().strftime('%A, %d %B %Y')}<br>"
        f"🕐 {datetime.now().strftime('%H:%M')} WIB</div>",
        unsafe_allow_html=True)

# ---- Koneksi & Auth ----
ws = connect_gsheet()

if not ws:
    st.error("❌ Koneksi ke Google Sheets gagal. Cek konfigurasi secrets.")
    st.stop()

if not pwd:
    st.markdown("""
    <div style='text-align:center;padding:100px 0;'>
      <div style='font-family:Sora,sans-serif;font-size:36px;font-weight:600;
                  color:#0a1628;margin-bottom:12px;letter-spacing:-1px;'>
        Strategy System
      </div>
      <div style='font-size:15px;color:#999;'>PT. Thea Theo Stationary</div>
      <div style='font-size:13px;color:#ccc;margin-top:20px;'>
        Masukkan password di sidebar untuk mulai →
      </div>
    </div>
    """, unsafe_allow_html=True)

elif access_type == "Admin (Setor Data)":
    admin_pwd = st.secrets.get("ADMIN_PASSWORD", "ike")
    if pwd == admin_pwd:
        halaman_admin(ws)
    else:
        st.error("❌ Password salah.")

elif access_type == "Master (Pak Asin)":
    if pwd == st.secrets["MASTER_PASSWORD"]:
        halaman_master(ws)
    else:
        st.error("❌ Password salah.")
