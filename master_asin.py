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

STATUS_OPTIONS = [
    "Menunggu Strategi",
    "Siap Eksekusi",
    "Sudah Dihubungi",
    "Kirim Sampel",
    "Deal / Goal",
    "Tidak Tertarik",
]

STATUS_COLOR = {
    "Menunggu Strategi": "🟡",
    "Siap Eksekusi": "🔵",
    "Sudah Dihubungi": "🟠",
    "Kirim Sampel": "🟣",
    "Deal / Goal": "🟢",
    "Tidak Tertarik": "🔴",
}

KOLOM_FIXED = ["Tanggal", "Perusahaan", "WA", "Link Maps", "Barang Umpan", "Status", "Catatan"]

# ==========================================
# 2. CSS KUSTOM
# ==========================================
st.set_page_config(page_title="TTS Strategy System", layout="wide", page_icon="📋")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #f8fafc !important; }

/* Metric cards */
div[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
div[data-testid="metric-container"] label { color: #64748b !important; font-size: 0.75rem !important; font-weight: 600 !important; letter-spacing: 0.05em; text-transform: uppercase; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 800 !important; color: #0f172a !important; }

/* Header badge */
.badge-master {
    display: inline-block;
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    color: white !important;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

/* Status pills in summary */
.pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    background: #f8fafc;
}

/* Buttons */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1e40af, #2563eb) !important;
    border: none !important;
}

/* Divider */
hr { border-color: #e2e8f0 !important; }

/* Table header */
.section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 4px;
    margin-top: 8px;
}

/* Warning / info box */
.info-box {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    color: #1e40af;
    font-size: 0.875rem;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_creds():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )

@st.cache_resource(ttl=60)
def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open("Antrean Penawaran TTS")
    except Exception as e:
        return None

def buat_link_wa(nomor, nama_pt):
    if not nomor or str(nomor).strip() in ["-", "", "None"]:
        return None
    nomor_bersih = "".join(filter(str.isdigit, str(nomor)))
    if nomor_bersih.startswith("0"):
        nomor_bersih = "62" + nomor_bersih[1:]
    elif nomor_bersih.startswith("8"):
        nomor_bersih = "62" + nomor_bersih
    pesan = (
        f"Halo, kami dari PT. THEA THEO STATIONARY (TTS). "
        f"Kami ingin menawarkan produk ATK terbaik untuk {nama_pt}. "
        f"Boleh kami kenalkan lebih lanjut?"
    )
    pesan_encoded = urllib.parse.quote(pesan)
    return f"https://wa.me/{nomor_bersih}?text={pesan_encoded}"

def load_dataframe(sheet):
    """Load semua data dari sheet, kembalikan df + raw_data."""
    raw_data = sheet.get_all_values()
    if len(raw_data) <= 1:
        return pd.DataFrame(columns=KOLOM_FIXED), raw_data
    df = pd.DataFrame(raw_data[1:], columns=KOLOM_FIXED[: len(raw_data[0])])
    # Pastikan semua kolom ada
    for col in KOLOM_FIXED:
        if col not in df.columns:
            df[col] = ""
    # Tambah row_number (= baris di gsheet, header = baris 1)
    df["_row"] = list(range(2, len(raw_data) + 1))
    return df, raw_data

def simpan_baris(sheet, row_num, row_data: dict):
    """Update satu baris di gsheet berdasarkan nomor baris (1-indexed)."""
    update_values = [
        [
            row_data.get("WA", ""),
            row_data.get("Link Maps", ""),
            row_data.get("Barang Umpan", ""),
            row_data.get("Status", ""),
            row_data.get("Catatan", ""),
        ]
    ]
    sheet.update(f"C{row_num}:G{row_num}", update_values)

def hapus_baris(sheet, row_num):
    """Hapus satu baris dari gsheet."""
    sheet.delete_rows(row_num)

def export_csv(df):
    """Return CSV string dari dataframe (tidak perlu library tambahan)."""
    return df.drop(columns=["_row", "Chat_WA"], errors="ignore").to_csv(index=False).encode("utf-8-sig")

# ==========================================
# 4. SIDEBAR LOGIN
# ==========================================
with st.sidebar:
    st.markdown(f"### 📋 {COMPANY_NAME}")
    st.markdown("---")
    access_type = st.radio(
        "Masuk sebagai:",
        ["🛡️ Master (Pak Asin)", "📥 Admin (Setor Data)"],
        index=0,
    )
    pwd = st.text_input("Password:", type="password", placeholder="Masukkan password...")
    st.markdown("---")
    st.caption(f"© {datetime.now().year} TTS Strategy System")

wb = connect_gsheet()

if not wb:
    st.error("❌ Koneksi Google Sheets gagal. Periksa konfigurasi secrets.")
    st.stop()

try:
    target_sheet = wb.worksheet("Riset_Pribadi_Asin")
except Exception:
    target_sheet = wb.get_worksheet(0)

# ==========================================
# 5. HALAMAN ADMIN
# ==========================================
if access_type == "📥 Admin (Setor Data)":
    if pwd == ADMIN_ENTRY_PWD:
        st.markdown('<div class="badge-master">MODE ADMIN</div>', unsafe_allow_html=True)
        st.title("📥 Form Setoran Data Prospek")
        st.markdown(
            '<div class="info-box">Isi data perusahaan yang sudah disurvei. Data akan langsung masuk ke dashboard Master untuk ditindaklanjuti.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        with st.form("form_admin", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                adm_nama = st.text_input("🏢 Nama Perusahaan *", placeholder="Contoh: CV Maju Bersama")
                adm_wa = st.text_input("📱 Nomor WA", placeholder="08xxxxxxxxxx")
            with c2:
                adm_maps = st.text_area("📍 Link Google Maps", placeholder="https://maps.google.com/...")
                adm_catatan = st.text_input("📝 Catatan Tambahan", placeholder="Opsional")

            submitted = st.form_submit_button("✅ Setor Data", use_container_width=True, type="primary")
            if submitted:
                if adm_nama.strip():
                    with st.spinner("Menyimpan data..."):
                        target_sheet.append_row(
                            [
                                datetime.now().strftime("%d/%m/%Y"),
                                adm_nama.strip(),
                                adm_wa,
                                adm_maps,
                                "-",
                                "Menunggu Strategi",
                                adm_catatan,
                            ]
                        )
                    st.success(f"✅ Data **{adm_nama}** berhasil disetor ke Master!")
                    st.balloons()
                else:
                    st.error("❌ Nama Perusahaan wajib diisi!")
    elif pwd != "":
        st.error("❌ Password salah.")
    else:
        st.info("Masukkan password untuk melanjutkan.")

# ==========================================
# 6. HALAMAN MASTER
# ==========================================
elif access_type == "🛡️ Master (Pak Asin)":
    if pwd == MASTER_PASSWORD:
        st.markdown('<div class="badge-master">MASTER DASHBOARD</div>', unsafe_allow_html=True)
        st.title("🛡️ Strategic Master Dashboard")

        df, raw_data = load_dataframe(target_sheet)

        # --- STATISTIK ---
        if not df.empty:
            total = len(df)
            deal = len(df[df["Status"] == "Deal / Goal"])
            belum = len(df[df["Status"] == "Menunggu Strategi"])
            proses = total - deal - belum
            pct_deal = round(deal / total * 100) if total > 0 else 0

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("📊 Total Prospek", total)
            c2.metric("🟡 Menunggu", belum)
            c3.metric("⚙️ In Progress", proses)
            c4.metric("🟢 Deal / Goal", deal)
            c5.metric("🎯 Conversion Rate", f"{pct_deal}%")
        else:
            st.info("Belum ada data prospek.")

        st.divider()

        # --- FORM INPUT MANDIRI ---
        with st.expander("➕ Input Riset Mandiri Pak Asin", expanded=False):
            with st.form("form_master", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    m_pt = st.text_input("🏢 Nama Perusahaan *")
                    m_wa = st.text_input("📱 Nomor WA")
                    m_maps = st.text_area("📍 Link Maps")
                with c2:
                    m_umpan = st.text_input("🎣 Barang Umpan")
                    m_status = st.selectbox("📌 Status Awal", STATUS_OPTIONS, index=1)
                    m_catatan = st.text_area("📝 Catatan Strategi")

                if st.form_submit_button("💾 Simpan ke Master", type="primary", use_container_width=True):
                    if m_pt.strip():
                        with st.spinner("Menyimpan..."):
                            target_sheet.append_row(
                                [
                                    datetime.now().strftime("%d/%m/%Y"),
                                    m_pt.strip(),
                                    m_wa,
                                    m_maps,
                                    m_umpan,
                                    m_status,
                                    m_catatan,
                                ]
                            )
                        st.success(f"✅ {m_pt} berhasil disimpan!")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("Nama Perusahaan wajib diisi!")

        # ==========================================
        # --- RISET OTOMATIS (GOOGLE CUSTOM SEARCH) ---
        # ==========================================
        with st.expander("🔍 Riset Prospek Otomatis — Google Search", expanded=False):
            st.markdown(
                '<div class="info-box">Cari perusahaan potensial menggunakan <b>Google Custom Search API</b> (gratis 100 query/hari). Sistem otomatis menilai potensi dan merekomendasikan barang umpan tiap perusahaan.</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                r_kota = st.text_input("📍 Kota / Wilayah", placeholder="Contoh: Jakarta Barat")
            with col_r2:
                r_industri = st.selectbox(
                    "🏭 Kategori Industri",
                    ["Semua", "Manufaktur", "Perbankan & Keuangan", "Rumah Sakit & Klinik",
                     "Hotel & Hospitality", "Pendidikan", "Properti & Konstruksi",
                     "Retail & Distribusi", "Logistik"],
                )

            if st.button("🚀 Mulai Riset Otomatis", type="primary", use_container_width=True):
                if not r_kota.strip():
                    st.warning("Masukkan kota/wilayah terlebih dahulu.")
                else:
                    import requests, re

                    # ---- SCORING ENGINE ----
                    SKOR_INDUSTRI = {
                        "bank": 95, "finance": 90, "asuransi": 88, "insurance": 88,
                        "rumah sakit": 92, "hospital": 92, "klinik": 85, "clinic": 85,
                        "hotel": 87, "hospitality": 85,
                        "sekolah": 83, "universitas": 85, "pendidikan": 80, "education": 80,
                        "manufaktur": 88, "manufacturing": 88, "pabrik": 86, "factory": 86,
                        "properti": 80, "property": 80, "konstruksi": 78, "construction": 78,
                        "logistik": 82, "logistics": 82, "ekspedisi": 80,
                        "retail": 75, "distributor": 78,
                        "teknologi": 77, "technology": 77,
                        "konsultan": 80, "consulting": 80,
                    }
                    UMPAN_INDUSTRI = {
                        "bank": "Kertas HVS A4 & Toner Printer",
                        "finance": "Map Snelhecter & Ordner",
                        "asuransi": "Kertas A4 & Ballpoint Box",
                        "rumah sakit": "Formulir Medis & Ballpoint",
                        "klinik": "Buku Rekam Medis & ATK",
                        "hotel": "Ballpoint Hotel & Notepad",
                        "sekolah": "Spidol Whiteboard & Penghapus",
                        "universitas": "Kertas A4 & Tinta Printer",
                        "manufaktur": "Buku Ekspedisi & Stempel",
                        "pabrik": "Form Produksi & Ballpoint Box",
                        "properti": "Map Proposal & Kertas HVS",
                        "konstruksi": "Buku Lapangan & Alat Ukur",
                        "logistik": "Label Pengiriman & Stempel",
                        "retail": "Struk Kasir & Ballpoint",
                        "teknologi": "Whiteboard & Spidol",
                        "konsultan": "Kertas A4 Premium & Folder",
                    }

                    def hitung_skor(nama, snippet, jenis):
                        teks = (nama + " " + snippet + " " + jenis).lower()
                        skor = 60
                        for kata, nilai in SKOR_INDUSTRI.items():
                            if kata in teks:
                                skor = max(skor, nilai)
                        if any(x in nama.upper() for x in ["PT ", "PT.", "TBK", "CV ", "CV."]):
                            skor = min(100, skor + 5)
                        return skor

                    def tebak_umpan(nama, snippet, jenis):
                        teks = (nama + " " + snippet + " " + jenis).lower()
                        for kata, umpan in UMPAN_INDUSTRI.items():
                            if kata in teks:
                                return umpan
                        return "Kertas HVS A4 & Ballpoint"

                    def skor_ke_estimasi(skor):
                        if skor >= 85: return "Tinggi"
                        if skor >= 72: return "Sedang"
                        return "Rendah"

                    def ekstrak_nama_pt(title, snippet):
                        for teks in [title, snippet]:
                            match = re.search(
                                r'\b(PT\.?\s+[\w\s&]+|CV\.?\s+[\w\s&]+|RS\s+[\w\s]+|Hotel\s+[\w\s]+|Bank\s+[\w\s]+)',
                                teks, re.IGNORECASE
                            )
                            if match:
                                nama = match.group(0).strip()
                                nama = re.sub(r'\s+', ' ', nama)[:50].strip()
                                if len(nama) > 5:
                                    return nama
                        return title.split(" - ")[0].split(" | ")[0][:50].strip()

                    # ---- CEK API KEY ----
                    SERP_KEY = st.secrets.get("SERPAPI_KEY", "")
                    if not SERP_KEY:
                        st.error(
                            "❌ **SERPAPI_KEY belum diset.**\n\n"
                            "Daftar gratis di [serpapi.com](https://serpapi.com) lalu tambahkan ke Streamlit Secrets:\n"
                            "```\nSERPAPI_KEY = \"abc123...\"\n```"
                        )
                    else:
                        industri_q = r_industri if r_industri != "Semua" else "perusahaan"
                        queries = [
                            f'PT {industri_q} "{r_kota}" Indonesia',
                            f'CV {industri_q} "{r_kota}" kantor',
                            f'perusahaan {industri_q} {r_kota} aktif lowongan',
                        ]

                        hasil_gabung = []
                        nama_sudah = set()

                        progress = st.progress(0, text="🔍 Mencari prospek...")
                        for qi, query in enumerate(queries):
                            try:
                                resp = requests.get(
                                    "https://serpapi.com/search",
                                    params={
                                        "api_key": SERP_KEY,
                                        "engine": "google",
                                        "q": query,
                                        "location": "Indonesia",
                                        "hl": "id",
                                        "gl": "id",
                                        "num": 10,
                                    },
                                    timeout=15,
                                )
                                data = resp.json()

                                if "error" in data:
                                    st.error(f"SerpAPI error: {data['error']}")
                                    break

                                # Ambil dari organic_results
                                items = data.get("organic_results", [])
                                for item in items:
                                    title   = item.get("title", "")
                                    snippet = item.get("snippet", "")
                                    nama    = ekstrak_nama_pt(title, snippet)

                                    if not nama or len(nama) < 4:
                                        continue
                                    if nama.lower() in nama_sudah:
                                        continue
                                    # Filter kasar — pastikan ada indikasi perusahaan
                                    teks_cek = (nama + snippet).upper()
                                    if not any(x in teks_cek for x in ["PT", "CV", "RS", "BANK", "HOTEL", "KLINIK", "SEKOLAH", "PERUSAHAAN", "COMPANY", "TBK"]):
                                        continue

                                    nama_sudah.add(nama.lower())
                                    skor = hitung_skor(nama, snippet, r_industri)
                                    hasil_gabung.append({
                                        "nama": nama,
                                        "jenis": r_industri if r_industri != "Semua" else "Perusahaan",
                                        "sumber": "Google (SerpAPI)",
                                        "skor_potensi": skor,
                                        "estimasi_kebutuhan": skor_ke_estimasi(skor),
                                        "barang_umpan": tebak_umpan(nama, snippet, r_industri),
                                        "alasan": snippet[:150] + "..." if len(snippet) > 150 else snippet,
                                    })

                            except Exception as e:
                                st.warning(f"Query {qi+1} gagal: {e}")

                            progress.progress((qi + 1) / len(queries), text=f"Query {qi+1}/{len(queries)} selesai...")

                        progress.empty()

                        if not hasil_gabung:
                            st.warning("⚠️ Tidak ada hasil. Coba ganti industri atau wilayah.")
                        else:
                            hasil_gabung.sort(key=lambda x: x["skor_potensi"], reverse=True)
                            seen = set()
                            unik = []
                            for p in hasil_gabung:
                                key = p["nama"].lower()[:20]
                                if key not in seen:
                                    seen.add(key)
                                    unik.append(p)
                            st.session_state["riset_hasil"] = unik
                            st.session_state["riset_kota"] = r_kota
                            st.success(f"✅ Ditemukan **{len(unik)} perusahaan** potensial di {r_kota}!")

            # ---- PANDUAN SETUP ----
            with st.expander("📖 Cara Setup SerpAPI (2 menit, gratis, tanpa kartu kredit)", expanded=False):
                st.markdown("""
**Langkah 1 — Daftar SerpAPI:**
1. Buka [serpapi.com](https://serpapi.com) → klik **"Get Started for Free"**
2. Daftar pakai email (tidak perlu kartu kredit)
3. Masuk ke dashboard → salin **API Key** di halaman utama

**Langkah 2 — Tambahkan ke Streamlit Secrets:**
```toml
SERPAPI_KEY = "abc123def456..."
```

**Limit gratis:** 100 pencarian/bulan. Tiap klik Riset = 3 pencarian → bisa **33x riset per bulan** gratis.
                """)


            # ---- TAMPILKAN HASIL RISET ----
            if "riset_hasil" in st.session_state and st.session_state["riset_hasil"]:
                hasil = st.session_state["riset_hasil"]
                kota_h = st.session_state.get("riset_kota", "")

                if "riset_selected" not in st.session_state or len(st.session_state["riset_selected"]) != len(hasil):
                    st.session_state["riset_selected"] = [False] * len(hasil)

                col_sa, col_sb, _ = st.columns([1, 1, 5])
                with col_sa:
                    if st.button("☑️ Pilih Semua", key="pilih_semua_riset"):
                        st.session_state["riset_selected"] = [True] * len(hasil)
                        st.rerun()
                with col_sb:
                    if st.button("🗑️ Reset Hasil", key="reset_riset"):
                        st.session_state.pop("riset_hasil", None)
                        st.session_state.pop("riset_selected", None)
                        st.rerun()

                color_map = {"Tinggi": "🟢", "Sedang": "🟡", "Rendah": "🔴"}
                sumber_map = {"Jobstreet": "🟣", "Yellow Pages": "🔵"}

                for i, p in enumerate(hasil):
                    badge = color_map.get(p["estimasi_kebutuhan"], "⚪")
                    src = sumber_map.get(p["sumber"], "⚫")
                    col_cb, col_info = st.columns([0.5, 9.5])
                    with col_cb:
                        st.session_state["riset_selected"][i] = st.checkbox(
                            "", value=st.session_state["riset_selected"][i], key=f"rcb_{i}"
                        )
                    with col_info:
                        st.markdown(
                            f"**{p['nama']}** &nbsp;{src} `{p['sumber']}` &nbsp;|&nbsp; {badge} **{p['estimasi_kebutuhan']}** &nbsp;|&nbsp; Skor: **{p['skor_potensi']}/100**<br>"
                            f"<small>🎣 Umpan: *{p['barang_umpan']}* &nbsp;·&nbsp; 💡 {p['alasan']}</small>",
                            unsafe_allow_html=True,
                        )
                    st.markdown("")

                dipilih = [p for i, p in enumerate(hasil) if st.session_state["riset_selected"][i]]
                if dipilih:
                    if st.button(f"➕ Tambah {len(dipilih)} Prospek ke Database", type="primary", use_container_width=True, key="tambah_riset"):
                        with st.spinner("Menyimpan ke Google Sheets..."):
                            for p in dipilih:
                                target_sheet.append_row([
                                    datetime.now().strftime("%d/%m/%Y"),
                                    p["nama"],
                                    "-",
                                    "-",
                                    p["barang_umpan"],
                                    "Menunggu Strategi",
                                    f"[{p['sumber']}] {p['jenis']} | Potensi: {p['estimasi_kebutuhan']} | {p['alasan']}",
                                ])
                        st.success(f"✅ {len(dipilih)} prospek berhasil ditambahkan ke database!")
                        st.session_state.pop("riset_hasil", None)
                        st.session_state.pop("riset_selected", None)
                        st.cache_resource.clear()
                        st.rerun()

        # --- FILTER & PENCARIAN ---
        if not df.empty:
            col_search, col_filter, col_export = st.columns([3, 2, 1])
            with col_search:
                cari = st.text_input("🔍 Cari Perusahaan / Catatan:", placeholder="Ketik nama PT...")
            with col_filter:
                filter_status = st.multiselect(
                    "Filter Status:",
                    options=STATUS_OPTIONS,
                    default=[],
                    placeholder="Semua status",
                )
            with col_export:
                st.markdown("<br>", unsafe_allow_html=True)
                df_export = df.copy()
                st.download_button(
                    "📥 Export CSV",
                    data=export_csv(df_export),
                    file_name=f"Prospek_TTS_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            # Apply filter
            df_view = df.copy()
            if cari:
                df_view = df_view[
                    df_view.apply(
                        lambda r: r.astype(str).str.contains(cari, case=False).any(), axis=1
                    )
                ]
            if filter_status:
                df_view = df_view[df_view["Status"].isin(filter_status)]

            # Tambah kolom WA link
            df_view["Chat_WA"] = df_view.apply(
                lambda x: buat_link_wa(x["WA"], x["Perusahaan"]), axis=1
            )

            # Tampilkan paling baru di atas (tanpa membuang _row!)
            df_view = df_view.sort_values("_row", ascending=False).reset_index(drop=True)

            st.markdown(f'<div class="section-title">📋 Daftar Prospek ({len(df_view)} data)</div>', unsafe_allow_html=True)

            edited_df = st.data_editor(
                df_view[["Tanggal", "Perusahaan", "WA", "Link Maps", "Barang Umpan", "Status", "Catatan", "Chat_WA", "_row"]],
                column_config={
                    "Chat_WA": st.column_config.LinkColumn("💬 Chat WA", display_text="Chat Sekarang 🟢"),
                    "Link Maps": st.column_config.LinkColumn("🗺️ Maps"),
                    "Status": st.column_config.SelectboxColumn(
                        "📌 Status",
                        options=STATUS_OPTIONS,
                        required=True,
                    ),
                    "Tanggal": st.column_config.TextColumn("📅 Tanggal", disabled=True),
                    "Perusahaan": st.column_config.TextColumn("🏢 Perusahaan"),
                    "WA": st.column_config.TextColumn("📱 WA"),
                    "Barang Umpan": st.column_config.TextColumn("🎣 Umpan"),
                    "Catatan": st.column_config.TextColumn("📝 Catatan", width="medium"),
                    "_row": None,  # Sembunyikan kolom internal
                },
                use_container_width=True,
                disabled=["Tanggal", "Chat_WA"],
                key="master_editor",
                num_rows="fixed",
            )

            col_save, col_del = st.columns([3, 1])

            with col_save:
                if st.button("💾 Simpan Semua Perubahan", type="primary", use_container_width=True):
                    with st.spinner("Menyimpan ke Google Sheets..."):
                        errors = []
                        for _, row in edited_df.iterrows():
                            try:
                                simpan_baris(target_sheet, int(row["_row"]), row.to_dict())
                            except Exception as e:
                                errors.append(str(e))
                        if errors:
                            st.error(f"Beberapa baris gagal disimpan: {errors}")
                        else:
                            st.success("✅ Semua perubahan berhasil disimpan!")
                    st.cache_resource.clear()
                    st.rerun()

            with col_del:
                # Fitur hapus berdasarkan nama PT
                with st.expander("🗑️ Hapus Data"):
                    nama_hapus = st.text_input("Nama PT yang akan dihapus:", key="del_input")
                    if st.button("❌ Hapus", type="secondary", use_container_width=True):
                        if nama_hapus.strip():
                            matched = df[df["Perusahaan"].str.lower() == nama_hapus.strip().lower()]
                            if not matched.empty:
                                row_to_del = int(matched.iloc[0]["_row"])
                                with st.spinner("Menghapus..."):
                                    hapus_baris(target_sheet, row_to_del)
                                st.success(f"✅ {nama_hapus} berhasil dihapus!")
                                st.cache_resource.clear()
                                st.rerun()
                            else:
                                st.error("Nama PT tidak ditemukan.")
                        else:
                            st.warning("Masukkan nama PT terlebih dahulu.")

            # --- RINGKASAN STATUS ---
            st.divider()
            st.markdown("#### 📊 Ringkasan per Status")
            status_counts = df["Status"].value_counts()
            cols = st.columns(len(STATUS_OPTIONS))
            for i, status in enumerate(STATUS_OPTIONS):
                count = status_counts.get(status, 0)
                emoji = STATUS_COLOR.get(status, "⚪")
                cols[i].metric(f"{emoji} {status}", count)

    elif pwd != "":
        st.error("❌ Password salah.")
    else:
        st.info("Masukkan password Master untuk membuka dashboard.")

else:
    st.info("Pilih mode akses dan masukkan password di sidebar.")
