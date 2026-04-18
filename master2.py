import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import urllib.parse
import json

# ==========================================
# KONFIGURASI
# ==========================================
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SHEET_NAME = "Antrean Penawaran TTS"
WORKSHEET_NAME = "Riset_Pribadi_Asin"

STATUS_OPTIONS = [
    "🕐 Menunggu Strategi",
    "🎯 Siap Eksekusi",
    "📞 Sudah Dihubungi",
    "📦 Kirim Sampel",
    "🤝 Deal / Goal",
    "❌ Tidak Tertarik",
]

KATEGORI_OPTIONS = [
    "Sekolah / Kampus",
    "Kantor Pemerintah",
    "Kantor Swasta",
    "Toko / Reseller",
    "Percetakan",
    "Lainnya",
]

SUMBER_OPTIONS = [
    "Kunjungan Lapangan",
    "Referral / Kenalan",
    "Marketplace",
    "Media Sosial",
    "Telepon Masuk",
    "Lainnya",
]

KOLOM = [
    "Tanggal Input", "Perusahaan", "PIC", "WA", "Alamat", "Link Maps",
    "Kategori", "Sumber", "Barang Umpan", "Status",
    "Follow Up Berikutnya", "Histori Catatan"
]

STATUS_COLOR = {
    "🕐 Menunggu Strategi": "#6B7280",
    "🎯 Siap Eksekusi":     "#2563EB",
    "📞 Sudah Dihubungi":   "#D97706",
    "📦 Kirim Sampel":      "#7C3AED",
    "🤝 Deal / Goal":       "#059669",
    "❌ Tidak Tertarik":    "#DC2626",
}

# ==========================================
# PAGE CONFIG & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="TTS · Sales Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0F172A;
    border-right: 1px solid #1E293B;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #94A3B8 !important;
}
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2 {
    color: #F1F5F9 !important;
}

/* Main background */
.main { background: #F8FAFC; }
.block-container { padding: 1.5rem 2rem 2rem !important; }

/* Metric cards */
.metric-row {
    display: flex; gap: 14px; margin-bottom: 1.5rem; flex-wrap: wrap;
}
.metric-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    flex: 1; min-width: 130px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s;
}
.metric-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.metric-num {
    font-size: 28px; font-weight: 700; color: #0F172A;
    font-family: 'DM Mono', monospace;
    line-height: 1.1; margin-bottom: 4px;
}
.metric-label {
    font-size: 12px; color: #64748B; font-weight: 500; letter-spacing: 0.04em;
    text-transform: uppercase;
}
.metric-accent { width: 36px; height: 4px; border-radius: 2px; margin-bottom: 10px; }

/* Status badge */
.badge {
    display: inline-block;
    padding: 3px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 600;
    letter-spacing: 0.02em;
}

/* Follow-up alert */
.fu-alert {
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-left: 4px solid #F97316;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
}
.fu-overdue {
    background: #FEF2F2;
    border-color: #FECACA;
    border-left-color: #EF4444;
}

/* Card prospek */
.prospect-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 12px;
    transition: box-shadow 0.2s, transform 0.15s;
}
.prospect-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.card-company { font-size: 17px; font-weight: 700; color: #0F172A; }
.card-pic { font-size: 13px; color: #64748B; margin: 2px 0 8px; }
.card-meta { font-size: 12px; color: #94A3B8; }

/* Header branding */
.brand-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex; align-items: center; gap: 16px;
}
.brand-title { color: white; font-size: 22px; font-weight: 700; margin: 0; }
.brand-sub { color: #94A3B8; font-size: 13px; margin: 0; }
.brand-logo {
    width: 48px; height: 48px; border-radius: 12px;
    background: #2563EB; display: flex; align-items: center;
    justify-content: center; font-size: 22px; flex-shrink: 0;
}

/* Form section */
.form-section {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* Divider */
.divider { height: 1px; background: #E2E8F0; margin: 1.5rem 0; }

/* Histori log */
.log-entry {
    background: #F8FAFC;
    border-left: 3px solid #CBD5E1;
    border-radius: 0 8px 8px 0;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-size: 13px; color: #475569;
}
.log-date { font-family: 'DM Mono', monospace; font-size: 11px; color: #94A3B8; }

/* Tombol WA */
.wa-btn {
    display: inline-block;
    background: #25D366;
    color: white !important;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 13px; font-weight: 600;
    text-decoration: none;
}

/* Scrollable table override */
.dataframe { font-size: 13px !important; }

/* Tab styling */
.stTabs [data-baseweb="tab"] {
    font-weight: 600; font-size: 14px;
}

/* Expander */
.streamlit-expanderHeader {
    font-weight: 600;
    font-size: 14px;
}

/* Alert box */
.stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# GOOGLE SHEETS
# ==========================================
def get_creds():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

@st.cache_resource(ttl=30)
def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open(SHEET_NAME)
    except Exception as e:
        st.error(f"Koneksi Google Sheets gagal: {e}")
        return None

def get_or_create_sheet(wb):
    try:
        ws = wb.worksheet(WORKSHEET_NAME)
    except:
        ws = wb.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=20)
        ws.append_row(KOLOM)
    return ws

def load_data(ws):
    raw = ws.get_all_values()
    if len(raw) <= 1:
        return pd.DataFrame(columns=KOLOM)
    df = pd.DataFrame(raw[1:], columns=KOLOM[:len(raw[0])])
    # Pastikan semua kolom ada
    for k in KOLOM:
        if k not in df.columns:
            df[k] = ""
    return df

def safe_update_row(ws, df_original, row_idx_original, updated_row_data):
    """Update baris berdasarkan index asli di dataframe (0-based = baris ke-2 di sheet)."""
    sheet_row = row_idx_original + 2  # +1 header, +1 gsheet 1-based
    ws.update(f"A{sheet_row}:L{sheet_row}", [updated_row_data])

def append_row(ws, row_data):
    ws.append_row(row_data)

# ==========================================
# HELPERS
# ==========================================
def buat_link_wa(nomor, nama_pt, pic=""):
    if not nomor or str(nomor).strip() in ["-", "", "None"]:
        return None
    nomor_bersih = ''.join(filter(str.isdigit, str(nomor)))
    if nomor_bersih.startswith('0'):
        nomor_bersih = '62' + nomor_bersih[1:]
    elif nomor_bersih.startswith('8'):
        nomor_bersih = '62' + nomor_bersih
    sapaan = f"Bapak/Ibu {pic}" if pic and pic not in ["-", ""] else f"Admin {nama_pt}"
    pesan = (
        f"Halo {sapaan}, saya dari PT. Thea Theo Stationary (TTS). "
        f"Kami ingin memperkenalkan produk alat tulis & stationary berkualitas untuk kebutuhan {nama_pt}. "
        f"Boleh kami berikan penawaran terbaik? Terima kasih 🙏"
    )
    return f"https://wa.me/{nomor_bersih}?text={urllib.parse.quote(pesan)}"

def tambah_log(histori_lama, catatan_baru):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    log_baru = f"[{timestamp}] {catatan_baru}"
    if histori_lama and histori_lama.strip() not in ["", "-"]:
        return histori_lama + "\n" + log_baru
    return log_baru

def parse_log(histori_str):
    if not histori_str or histori_str.strip() in ["", "-"]:
        return []
    return [l.strip() for l in histori_str.strip().split("\n") if l.strip()]

def status_color(status):
    return STATUS_COLOR.get(status, "#6B7280")

def hitung_metrics(df):
    total = len(df)
    deal = len(df[df["Status"] == "🤝 Deal / Goal"])
    aktif = len(df[df["Status"].isin(["🎯 Siap Eksekusi", "📞 Sudah Dihubungi", "📦 Kirim Sampel"])])
    menunggu = len(df[df["Status"] == "🕐 Menunggu Strategi"])
    # Follow up hari ini / lewat
    today = date.today()
    fu_list = []
    for _, r in df.iterrows():
        fu = r.get("Follow Up Berikutnya", "")
        if fu and fu not in ["-", ""]:
            try:
                fu_date = datetime.strptime(fu, "%d/%m/%Y").date()
                if fu_date <= today and r["Status"] not in ["🤝 Deal / Goal", "❌ Tidak Tertarik"]:
                    fu_list.append((r, fu_date))
            except:
                pass
    return total, deal, aktif, menunggu, fu_list

# ==========================================
# SIDEBAR LOGIN
# ==========================================
wb = connect_gsheet()

with st.sidebar:
    st.markdown(f"### 📋 TTS Sales System")
    st.markdown("---")
    access_type = st.radio(
        "Masuk sebagai:",
        ["🛡️ Master (Pak Asin)", "📥 Admin (Setor Data)"],
        label_visibility="collapsed"
    )
    pwd = st.text_input("Password", type="password", placeholder="Masukkan password...")
    st.markdown("---")

    # Cek login
    is_master = (access_type == "🛡️ Master (Pak Asin)" and pwd == st.secrets["ADMIN_PASSWORD"])
    is_admin  = (access_type == "📥 Admin (Setor Data)" and pwd == st.secrets.get("ADMIN_ENTRY_PWD", "ike"))

    if is_master:
        st.success("✅ Login Master")
    elif is_admin:
        st.success("✅ Login Admin")
    elif pwd:
        st.error("❌ Password salah")

    st.markdown("---")
    st.markdown(f"<small style='color:#475569;'>© 2025 {COMPANY_NAME}</small>
