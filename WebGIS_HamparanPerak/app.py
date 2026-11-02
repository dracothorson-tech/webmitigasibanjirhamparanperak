import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import fitz
from PIL import Image

ROOT = Path(__file__).parent
MAP_DIR = ROOT / "data" / "peta"
DB_DIR = ROOT / "data" / "database"
DOC_DIR = ROOT / "data" / "dokumentasi"

st.set_page_config(page_title="WebGIS Mitigasi Banjir | Hamparan Perak", page_icon="🗺️", layout="wide")

NAVY = "#061A3A"
BLUE = "#0B5CAB"
GREEN = "#5DBB63"
st.markdown(f"""
<style>
.stApp {{ background:#f3f5f8; }}
[data-testid="stSidebar"] {{ background:linear-gradient(180deg,#09213e,#123653); }}
[data-testid="stSidebar"] * {{ color:white !important; }}
.topbar {{ background:linear-gradient(90deg,{NAVY},{BLUE}); color:white; padding:18px 22px;
border-radius:10px; margin-bottom:14px; }}
.panel {{ background:white; padding:14px 16px; border:1px solid #e0e5ec; border-radius:10px; }}
.small {{ color:#526174; font-size:13px; }}
div[data-testid="stMetric"] {{ background:white; border:1px solid #e0e5ec; padding:12px; border-radius:9px; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="topbar">
<h3 style="margin:0">STRATEGI MITIGASI BANJIR BERBASIS CERDAS</h3>
<div>Integrasi CA-ANN dalam Pemodelan Risiko Spasial Lahan di Kecamatan Hamparan Perak</div>
</div>
""", unsafe_allow_html=True)

def read_excel():
    files = list(DB_DIR.glob("*.xlsx")) + list(DB_DIR.glob("*.xls"))
    if not files:
        return None, None
    try:
        xls = pd.ExcelFile(files[0])
        sheets = {s: pd.read_excel(files[0], sheet_name=s) for s in xls.sheet_names}
        return files[0].name, sheets
    except Exception as e:
        st.error(f"Gagal membaca Excel: {e}")
        return None, None

def find_map(year):
    candidates = [MAP_DIR / f"{year}.jpg", MAP_DIR / f"{year}.jpeg", MAP_DIR / f"{year}.png"]
    for p in candidates:
        if p.exists():
            return p
    return None

def show_map(year, caption=None):
    p = find_map(year)
    if p:
        st.image(str(p), use_container_width=True, caption=caption or f"Peta penggunaan lahan {year}")
    else:
        st.info(f"File peta {year} belum tersedia. Simpan sebagai data/peta/{year}.jpg (atau .jpeg/.png).")

def norm_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

with st.sidebar:
    st.markdown("## 🗺️ WEBGIS")
    page = st.radio("Navigasi", ["Dashboard", "Peta Historis", "Peta Proyeksi 2040",
                                  "Statistik Perubahan", "Risiko Banjir", "Dokumentasi", "Informasi Wilayah"])
    st.markdown("---")
    st.caption("Hamparan Perak • Deli Serdang")

filename, sheets = read_excel()

if page == "Dashboard":
    st.subheader("Dashboard")
    a,b,c,d = st.columns(4)
    a.metric("Peta historis", "2010–2025")
    b.metric("Peta proyeksi", "2040")
    c.metric("Basis data", "Excel")
    d.metric("Dokumentasi", "PDF")
    left,right = st.columns([2.2,1])
    with left:
        st.markdown("#### Peta penggunaan lahan")
        year = st.selectbox("Pilih tahun peta", [2010,2015,2020,2025,2040], index=3)
        show_map(year)
    with right:
        st.markdown("#### Ringkasan perubahan lahan")
        if sheets and "Perubahan_Lahan" in sheets:
            df = norm_cols(sheets["Perubahan_Lahan"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Isi sheet Excel bernama `Perubahan_Lahan` untuk menampilkan ringkasan.")
        st.markdown("#### Informasi")
        st.write("Dashboard menampilkan peta JPG statis dan statistik yang dibaca dari Excel.")

elif page == "Peta Historis":
    st.subheader("Peta Historis Penggunaan Lahan")
    year = st.select_slider("Tahun", options=[2010,2015,2020,2025], value=2025)
    show_map(year, f"Peta penggunaan lahan Kecamatan Hamparan Perak — {year}")

elif page == "Peta Proyeksi 2040":
    st.subheader("Peta Proyeksi Perubahan Lahan 2040")
    show_map(2040, "Peta proyeksi penggunaan lahan tahun 2040")
    if sheets and "Proyeksi_2040" in sheets:
        st.markdown("#### Ringkasan proyeksi")
        st.dataframe(norm_cols(sheets["Proyeksi_2040"]), use_container_width=True, hide_index=True)

elif page == "Statistik Perubahan":
    st.subheader("Statistik Perubahan Penggunaan Lahan")
    if sheets and "Perubahan_Lahan" in sheets:
        df = norm_cols(sheets["Perubahan_Lahan"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        # Chart defaults: columns Kelas_Lahan, Tahun, Luas_ha; or Kelas_Lahan, 2010, 2025
        cols = {c.lower(): c for c in df.columns}
        if {"kelas_lahan","tahun","luas_ha"}.issubset(cols):
            plotdf = df.rename(columns={cols["kelas_lahan"]:"Kelas Lahan",cols["tahun"]:"Tahun",cols["luas_ha"]:"Luas (ha)"})
            fig = px.bar(plotdf, x="Kelas Lahan", y="Luas (ha)", color="Tahun", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        elif "kelas_lahan" in cols:
            numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if numeric:
                longdf = df.melt(id_vars=[cols["kelas_lahan"]], value_vars=numeric, var_name="Tahun", value_name="Luas (ha)")
                fig = px.bar(longdf, x=cols["kelas_lahan"], y="Luas (ha)", color="Tahun", barmode="group")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Untuk grafik otomatis, gunakan kolom Kelas_Lahan dan kolom luas per tahun, misalnya 2010, 2015, 2020, 2025, 2040.")
    else:
        st.warning("Sheet `Perubahan_Lahan` belum ditemukan pada Excel.")

elif page == "Risiko Banjir":
    st.subheader("Risiko Banjir")
    show_map("Risiko_2025", "Peta risiko banjir 2025")
    if sheets and "Risiko_Banjir" in sheets:
        df = norm_cols(sheets["Risiko_Banjir"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        cols = {c.lower(): c for c in df.columns}
        if "kelas_risiko" in cols and "luas_ha" in cols:
            fig = px.pie(df, names=cols["kelas_risiko"], values=cols["luas_ha"], hole=.55)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Opsional: tambahkan sheet `Risiko_Banjir` berisi Kelas_Risiko dan Luas_ha.")

elif page == "Dokumentasi":
    st.subheader("Dokumentasi dan Narasi Penelitian")
    pdfs = sorted(DOC_DIR.glob("*.pdf"))
    if not pdfs:
        st.info("Letakkan buku/laporan PDF di folder data/dokumentasi/.")
    else:
        selected = st.selectbox("Pilih dokumen", pdfs, format_func=lambda x: x.name)
        st.download_button("Unduh PDF", data=selected.read_bytes(), file_name=selected.name, mime="application/pdf")
        doc = fitz.open(selected)
        pages = {f"Halaman {i+1}": i for i in range(len(doc))}
        page_label = st.selectbox("Pilih halaman untuk dibaca", list(pages))
        page_text = doc[pages[page_label]].get_text().strip()
        if page_text:
            st.text_area("Isi halaman", page_text, height=320)
        else:
            st.warning("Halaman ini mungkin berupa hasil scan. Teks belum dapat diekstrak otomatis; gunakan PDF yang memiliki OCR.")
        with st.expander("Tampilkan daftar isi/teks ringkas dokumen"):
            for i in range(min(len(doc), 8)):
                txt = doc[i].get_text().strip()
                if txt:
                    st.markdown(f"**Halaman {i+1}**")
                    st.write(txt[:1800] + ("…" if len(txt)>1800 else ""))

elif page == "Informasi Wilayah":
    st.subheader("Informasi Wilayah")
    if sheets and "Informasi_Wilayah" in sheets:
        st.dataframe(norm_cols(sheets["Informasi_Wilayah"]), use_container_width=True, hide_index=True)
    else:
        st.info("Isi sheet `Informasi_Wilayah` pada Excel dengan kolom Informasi dan Nilai.")
    st.markdown("#### Tentang aplikasi")
    st.write("WebGIS ini menyajikan peta tematik statis dalam format gambar JPG/PNG. Tabel dan grafik berasal dari database Excel; tidak melakukan pemrosesan spasial langsung.")

st.markdown("---")
st.caption("WebGIS Mitigasi Banjir Berbasis Cerdas — Hamparan Perak | Peta dan statistik mengikuti data yang disediakan.")
