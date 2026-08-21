"""
BhuDrishti — Farmers Desk
AI-powered fertility, water resources, and land assessment.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import folium
from streamlit_folium import st_folium

from bhunaksha_client import list_districts, list_tehsils, fetch_plot_real
from geo_utils import create_geodataframe, get_centroid, get_area_sqm
from fertility_water import estimate_fertility, detect_water_resources
from ai_report import generate_ai_report
from aasia import summarize_page

st.set_page_config(page_title="Farmers Desk | BhuDrishti", page_icon="🌾", layout="wide")

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.farm-hero {
    background: linear-gradient(120deg, #1b5e20, #2e7d32, #388e3c);
    color: #fff !important; padding: 20px 24px; border-radius: 12px; margin-bottom: 18px;
}
.farm-hero h2 { color: #fff !important; margin: 0 0 4px 0; }
.farm-hero .sub { color: #c8e6c9 !important; font-size: 0.9rem; }
.info-card {
    background: #fff; border-radius: 10px; padding: 16px 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08); border-left: 5px solid #2e7d32;
    margin-bottom: 10px;
}
.info-card h4 { color: #1b5e20 !important; margin: 0 0 8px 0; }
.info-card p, .info-card li { color: #2d4a2d !important; margin: 3px 0; font-size: 0.92rem; }
.water-card {
    background: #e3f2fd; border-radius: 10px; padding: 16px 18px;
    border-left: 5px solid #1565c0; margin-bottom: 10px;
}
.water-card h4 { color: #0d47a1 !important; margin: 0 0 8px 0; }
.water-card p { color: #1a237e !important; font-size: 0.92rem; }
.ai-badge {
    display: inline-block; background: #e8f5e9; color: #1b5e20 !important;
    border: 1px solid #a5d6a7; border-radius: 12px;
    padding: 2px 10px; font-size: 0.78rem; font-weight: 600; margin-bottom: 8px;
}
.gov-note {
    background: #fff8e1; border: 1px solid #f9a825; border-radius: 8px;
    padding: 10px 14px; color: #5d4037 !important; font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="farm-hero">
  <h2>🌾 Farmers Desk — Agricultural Land Assessment</h2>
  <div class="sub">Live Bhunaksha plot data · AI Soil Fertility · Water Resources · Land Report</div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k in ["farm_result", "farm_fert", "farm_water", "farm_report"]:
    if k not in st.session_state:
        st.session_state[k] = None


# ── District / Tehsil dropdowns (live from Bhunaksha) ─────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_districts():
    try:
        items = list_districts()
        return {f"{it.get('value')} ({it.get('code')})": str(it.get("code")) for it in items}
    except Exception:
        return {"प्रयागराज (175)": "175", "आगरा (146)": "146"}

@st.cache_data(ttl=1800, show_spinner=False)
def load_tehsils(district_code: str):
    try:
        items = list_tehsils(district_code)
        return {f"{it.get('value')} ({it.get('code')})": str(it.get("code")) for it in items}
    except Exception:
        return {}


st.markdown("### Step 1 — Select Plot")

districts = load_districts()
d_labels  = list(districts.keys())
d_default = next((i for i, l in enumerate(d_labels) if "175" in l or "प्रयाग" in l), 0)
d_label   = st.selectbox("District", d_labels, index=d_default)
d_code    = districts[d_label]

tehsils = load_tehsils(d_code)
if tehsils:
    t_labels  = list(tehsils.keys())
    t_default = next((i for i, l in enumerate(t_labels) if "00895" in l or "कोरांव" in l), 0)
    t_label   = st.selectbox("Tehsil", t_labels, index=min(t_default, len(t_labels) - 1))
    t_code    = tehsils[t_label]
else:
    t_code  = st.text_input("Tehsil code", "00895")
    t_label = t_code

col1, col2, col3 = st.columns(3)
with col1:
    v_code  = st.text_input("Village code", "163668")
with col2:
    v_name  = st.text_input("Village name", "कूदर / Koodar")
with col3:
    plot_no = st.text_input("Plot No", "30")

# ── Fetch & Analyse ──────────────────────────────────────────────────────────
if st.button("🌾 Get Farm Insights", type="primary", use_container_width=True):
    try:
        with st.spinner("Fetching live plot data from Bhunaksha..."):
            data   = fetch_plot_real(
                str(d_code).strip(), str(t_code).strip(),
                str(v_code).strip(), str(plot_no).strip(),
            )
            coords = [[float(lo), float(la)] for lo, la in data["coordinates"]]
            gdf    = create_geodataframe(coords, plot_no)
            area   = get_area_sqm(gdf)
            lat, lon = get_centroid(gdf)

            st.session_state.farm_result = {
                "district": d_label, "tehsil": t_label,
                "village": v_name or v_code, "plot_no": str(plot_no),
                "coords": coords, "area": area, "lat": lat, "lon": lon,
                "gis_code": data.get("gis_code"),
                "info_text": data.get("info_text", ""),
            }

        with st.spinner("Running AI fertility & water analysis..."):
            st.session_state.farm_fert   = estimate_fertility(coords)
            st.session_state.farm_water  = detect_water_resources(coords)
            st.session_state.farm_report = generate_ai_report(
                plot_no,
                st.session_state.farm_fert,
                st.session_state.farm_water,
            )

    except Exception as e:
        st.error(f"Failed to fetch plot data: {e}")
        st.info("Tip: Make sure Village code and Plot No are correct for the selected District/Tehsil.")
        st.session_state.farm_result = None

# ── Results ──────────────────────────────────────────────────────────────────
if st.session_state.farm_result:
    r     = st.session_state.farm_result
    fert  = st.session_state.farm_fert  or {}
    water = st.session_state.farm_water or {}
    rep   = st.session_state.farm_report or {}

    st.success(f"Plot {r['plot_no']} · {r['village']} · GIS `{r.get('gis_code')}`")

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Village",  r["village"])
    m2.metric("Plot No",  r["plot_no"])
    m3.metric("Area",     f"{r['area']:,.0f} sq.m")
    m4.metric("Centroid", f"{r['lat']:.4f}, {r['lon']:.4f}")

    st.markdown("---")

    # Map + Corners
    latlon = [[la, lo] for lo, la in r["coords"]]
    fmap = folium.Map(
        location=[r["lat"], r["lon"]], zoom_start=18,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
    )
    folium.Polygon(
        latlon, color="#1b5e20", weight=3,
        fill=True, fill_color="#76ff03", fill_opacity=0.3,
    ).add_to(fmap)
    for i, (la, lo) in enumerate(latlon[:-1], 1):
        folium.CircleMarker(
            [la, lo], radius=5, color="white", fill=True,
            fill_color="#1b5e20", popup=f"P{i}",
        ).add_to(fmap)

    map_col, corner_col = st.columns([1.4, 1])
    with map_col:
        st.subheader("Satellite View")
        st_folium(fmap, height=380, key=f"farm_map_{r['plot_no']}_{r.get('gis_code')}")
    with corner_col:
        st.subheader("Corner Coordinates")
        for i, (lo, la) in enumerate(r["coords"], 1):
            st.write(f"**P{i}:** `{la:.6f}`, `{lo:.6f}`")
        if r.get("info_text"):
            st.text_area("Bhunaksha Info", r["info_text"], height=100)

    st.markdown("---")
    st.markdown("### Step 2 — AI Land Assessment")

    # Fertility + Water side by side
    fa_col, wa_col = st.columns(2)

    with fa_col:
        src = fert.get("source", "")
        badge = "Mistral AI" if "Mistral" in src else "Prototype Estimate"
        st.markdown(f'<div class="ai-badge">🌱 {badge}</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown(f"**🌱 Soil Fertility (Upjau)**")
        level = fert.get("level", "Medium") if isinstance(fert, dict) else "—"
        color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(level, "⚪")
        st.markdown(f"### {color} {level}")
        if isinstance(fert, dict):
            st.write(fert.get("reason", ""))
            if fert.get("crop_suitability"):
                st.markdown(f"**Suitable Crops:** {fert['crop_suitability']}")
            if fert.get("ndvi_note"):
                st.caption(f"📡 {fert['ndvi_note']}")
        else:
            st.write(fert)
        st.markdown("</div>", unsafe_allow_html=True)

    with wa_col:
        src_w = water.get("source", "") if isinstance(water, dict) else ""
        badge_w = "Mistral AI" if "Mistral" in src_w else "Prototype Estimate"
        st.markdown(f'<div class="ai-badge">💧 {badge_w}</div>', unsafe_allow_html=True)
        st.markdown('<div class="water-card">', unsafe_allow_html=True)
        st.markdown("**💧 Water Resources**")
        if isinstance(water, dict):
            st.markdown(f"**Nearby:** {water.get('nearby_water', '—')}")
            st.write(water.get("note", ""))
            if water.get("irrigation_hint"):
                st.info(water["irrigation_hint"])
            if water.get("water_table_depth"):
                st.markdown(f"**Water Table:** {water['water_table_depth']}")
        else:
            st.write(water)
        st.markdown("</div>", unsafe_allow_html=True)

    # AI Land Report
    if isinstance(rep, dict):
        st.markdown("---")
        st.markdown("### Step 3 — AI Land Report")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"**Land Use:** {rep.get('land_use', '—')}")
            st.markdown(f"**Structures:** {rep.get('structures', '—')}")
        with r2:
            st.markdown(f"**Fertility (AI):** {rep.get('fertility_indication', '—')}")
            st.markdown(f"**Water (AI):** {rep.get('water_resources', '—')}")
        if rep.get("summary"):
            st.success(f"📋 {rep['summary']}")
        if rep.get("error"):
            st.caption(f"Vision note: {rep['error']}")

    st.markdown("---")
    st.markdown('<div class="gov-note">⚠️ <b>Official Notice:</b> These assessments are AI-generated awareness estimates only. '
                'They are NOT official soil health certifications. For authoritative soil testing, '
                'contact your nearest Krishi Vigyan Kendra or State Agriculture Department.</div>',
                unsafe_allow_html=True)

# ── AASIA ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🤖 AASIA — Agricultural Assistant")
if st.button("Get Official Farmers Desk Guidance", use_container_width=True):
    with st.spinner("AASIA is preparing guidance..."):
        st.info(summarize_page("Farmers"))
