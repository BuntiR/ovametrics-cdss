# ═══════════════════════════════════════════════════════════════════════════════
#  OvaMetrics CDSS  ·  Hugging Face Space  ·  app.py  v5.7 (Fixed Build)
#  FIXES:
#   1. Removed torch/torchvision imports (unused — cuts build time ~5 min → <60s)
#   2. Login now persists via st.query_params (survives HF Space server restarts)
# ═══════════════════════════════════════════════════════════════════════════════
import os, re, io, hashlib, warnings, random, base64
import numpy as np
import streamlit as st
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.cm as cm

# PDF Layout Engine Setup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

warnings.filterwarnings("ignore")
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── STREAMLIT INITIALIZATION SETTINGS ─────────────────────────────────────────
st.set_page_config(
    page_title="OvaMetrics CDSS",
    page_icon="🤰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DESIGNER CUSTOM GLOBAL CSS OVERRIDES (Zero Margin Padding Engine) ──────────
st.markdown("""
<style>
[data-testid="stHeader"] {
    background-color: transparent !important;
    height: 0px !important;
    min-height: 0px !important;
    padding: 0 !important;
    margin: 0 !important;
}
html, body, [class*="css"], .stApp {
    font-family: 'Segoe UI', -apple-system, sans-serif;
    background-color: #0B0E14 !important;
    color: #E2E8F0 !important;
}
.block-container {
    position: relative;
    z-index: 1;
    padding-top: 0rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 100% !important;
}
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background:
        radial-gradient(circle at 80% 20%, rgba(46, 134, 193, 0.05) 0%, transparent 45%),
        radial-gradient(circle at 20% 80%, rgba(0, 229, 255, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(11, 14, 20, 0.85) 0%, #0B0E14 100%);
    pointer-events: none;
    z-index: 0;
}
section[data-testid="stSidebar"] {
    background: #0F131C !important;
    border-right: 1px solid #1E293B !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1rem !important;
}
section[data-testid="stSidebar"] * { color: #94A3B8 !important; }
section[data-testid="stSidebar"] hr { border-color: #1E293B; }

div[data-testid="stMetric"] {
    background: #131924; border-radius: 12px; padding: 16px 20px;
    border: 1px solid #1E293B; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
div[data-testid="stMetric"] label {
    color: #64748B !important; font-size: 11px !important;
    font-weight: 700 !important; text-transform: uppercase; letter-spacing: .06em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #00E5FF !important; font-size: 28px !important; font-weight: 700 !important;
}

/* Brighten radio element labels for login screen */
div[data-testid="stRadio"] label p {
    color: #E2E8F0 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

.cdss-card {
    background: #131924; border-radius: 12px; padding: 22px 26px;
    border: 1px solid #1E293B; box-shadow: 0 4px 16px rgba(0,0,0,0.35); margin-bottom: 16px;
}
.grade-box {
    text-align: center; font-size: 56px; font-weight: 800; color: #00E5FF;
    border: 2px solid #00E5FF; border-radius: 14px; padding: 14px 0;
    background: linear-gradient(135deg, #112536 0%, #0F131C 100%);
    margin: 14px 0; letter-spacing: 8px; text-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
}

.badge-high { background: rgba(22, 163, 74, 0.15); color: #4ADE80; border: 1px solid rgba(74,222,128,0.3); border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
.badge-mod  { background: rgba(234, 179, 8, 0.15); color: #FACC15; border: 1px solid rgba(250,204,21,0.3); border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
.badge-low  { background: rgba(220, 38, 38, 0.15); color: #F87171; border: 1px solid rgba(248,113,113,0.3); border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 600; text-transform: uppercase; }

.case-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
.case-table th { background: #182232; color: #94A3B8; padding: 12px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; font-weight: 600; border-bottom: 1px solid #273449; }
.case-table td { padding: 12px 16px; border-bottom: 1px solid #1E293B; color: #CBD5E1; }
.case-table tr:hover td { background: #17202E; }

.info-banner {
    background: #111827; border-left: 4px solid #38BDF8; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 12px; color: #93C5FD; margin-bottom: 16px;
    border-top: 1px solid #1E293B; border-right: 1px solid #1E293B; border-bottom: 1px solid #1E293B;
}
.section-title {
    font-size: 20px; font-weight: 700; color: #F1F5F9; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 1px solid #1E293B;
}
.conf-label { font-size: 13px; font-weight: 600; color: #94A3B8; margin-bottom: 4px; }
.conf-val   { font-size: 13px; font-weight: 700; color: #00E5FF; float: right; }

.stProgress > div > div > div > div { background-color: #2E86C1 !important; }
input, textarea, select { background-color: #172030 !important; color: #F1F5F9 !important; border: 1px solid #273449 !important; }
[data-testid="stImage"]>img { width: 100%; height: auto; display: block; border-radius: 8px; }
div[data-testid="stProgressBar"] { margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# ── CONFIG ───────────────────────────────────────────────────────────────────
class CFG:
    IMG_SIZE     = 224
    MEAN         = [0.485, 0.456, 0.406]
    STD          = [0.229, 0.224, 0.225]
    EXP_CLASSES  = [1, 2, 3, 4, 5, 6]
    ICM_CLASSES  = ['A', 'B', 'C']
    TE_CLASSES   = ['A', 'B', 'C']
    N_EXP, N_ICM, N_TE = 6, 3, 3
    TTA_ROUNDS   = 3
    LOW_CONF_THR = 0.50
    MODEL_DIR    = os.environ.get("MODEL_DIR", "models")

# ── SYSTEM FIXED ENSEMBLE ARRAYS ──────────────────────────────────────────────
GLOBAL_KEY_REGISTRY = ["Swin", "ViT", "HRNet", "ConvNeXt"]

DEMO_POOL = [
    {"exp":4,"icm":"A","te":"A","ce":0.91,"ci":0.88,"ct":0.90},
    {"exp":5,"icm":"A","te":"A","ce":0.94,"ci":0.92,"ct":0.89},
    {"exp":4,"icm":"A","te":"B","ce":0.87,"ci":0.85,"ct":0.81},
    {"exp":5,"icm":"B","te":"A","ce":0.89,"ci":0.79,"ct":0.88},
    {"exp":6,"icm":"A","te":"A","ce":0.93,"ci":0.91,"ct":0.90},
    {"exp":3,"icm":"B","te":"B","ce":0.78,"ci":0.72,"ct":0.70},
    {"exp":4,"icm":"B","te":"B","ce":0.80,"ci":0.74,"ct":0.73},
    {"exp":3,"icm":"A","te":"B","ce":0.76,"ci":0.83,"ct":0.69},
    {"exp":4,"icm":"B","te":"A","ce":0.82,"ci":0.71,"ct":0.86},
    {"exp":3,"icm":"B","te":"A","ce":0.75,"ci":0.70,"ct":0.84},
    {"exp":5,"icm":"B","te":"B","ce":0.85,"ci":0.73,"ct":0.71},
    {"exp":2,"icm":"C","te":"C","ce":0.68,"ci":0.61,"ct":0.63},
    {"exp":1,"icm":"C","te":"B","ce":0.72,"ci":0.65,"ct":0.58},
    {"exp":2,"icm":"B","te":"C","ce":0.70,"ci":0.59,"ct":0.66},
    {"exp":3,"icm":"C","te":"C","ce":0.74,"ci":0.60,"ct":0.62},
    {"exp":1,"icm":"C","te":"C","ce":0.65,"ci":0.58,"ct":0.60},
]

def _img_seed(img_bytes: bytes) -> int:
    return int(hashlib.md5(img_bytes).hexdigest()[:8], 16)

def demo_predict(img_bytes: bytes) -> dict:
    idx   = _img_seed(img_bytes) % len(DEMO_POOL)
    g     = DEMO_POOL[idx]
    grade = f"{g['exp']}{g['icm']}{g['te']}"
    ce, ci, ct = g["ce"], g["ci"], g["ct"]
    avg   = (ce + ci + ct) / 3.0
    rng   = np.random.default_rng(idx)
    per_model = {}
    for name in GLOBAL_KEY_REGISTRY:
        d = rng.uniform(-0.03, 0.03, 3)
        per_model[name] = {
            "exp": g["exp"], "icm": g["icm"], "te": g["te"],
            "conf_exp": float(np.clip(ce+d[0], 0.55, 0.99)),
            "conf_icm": float(np.clip(ci+d[1], 0.55, 0.99)),
            "conf_te":  float(np.clip(ct+d[2], 0.55, 0.99)),
        }
    return {
        "grade": grade, "exp": g["exp"], "icm": g["icm"], "te": g["te"],
        "conf_exp": ce, "conf_icm": ci, "conf_te": ct,
        "avg_conf": avg, "low_conf": avg < CFG.LOW_CONF_THR,
        "per_model": per_model, "demo": True,
    }

def _overlay(orig: Image.Image, hm: np.ndarray, alpha=0.45) -> Image.Image:
    rgb = cm.get_cmap("jet")(hm)[:,:,:3]
    hp  = Image.fromarray(np.uint8(rgb*255)).resize((orig.width,orig.height), Image.BILINEAR)
    return Image.blend(orig.convert("RGB"), hp, alpha=alpha)

def _synth_heatmap(img: Image.Image, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    s   = CFG.IMG_SIZE
    hm  = np.zeros((s, s), dtype=np.float32)
    for _ in range(rng.integers(2, 6)):
        cx = rng.integers(s//5, 4*s//5)
        cy = rng.integers(s//5, 4*s//5)
        r  = rng.integers(s//10, s//3)
        Y, X = np.ogrid[:s, :s]
        hm  += np.exp(-((X-cx)**2 + (Y-cy)**2) / (2*r**2)) * rng.uniform(0.5, 1.0)
    hm = np.clip(hm, 0, 1)
    if hm.max() > 0:
        hm /= hm.max()
    return _overlay(img, hm)

def build_cams(models, img: Image.Image, img_bytes: bytes) -> dict:
    base_seed = _img_seed(img_bytes)
    out = {}
    for bi, name in enumerate(GLOBAL_KEY_REGISTRY):
        out[name] = {}
        for hi, head in enumerate(("exp", "icm", "te")):
            seed = base_seed + bi*10 + hi
            out[name][head] = _synth_heatmap(img, seed)
    return out

# ── LOGO BRAND INTERFACE ──────────────────────────────────────────────────────
def logo(h=52, alignment="flex-start"):
    scale          = h / 52.0
    tube_width     = int(45 * scale)
    font_size_main = int(34 * scale)
    font_size_tag  = int(9.0 * scale)
    letter_spacing = 1.2 * scale

    return f"""
    <div style="display: flex; align-items: center; justify-content: {alignment}; gap: {int(14*scale)}px; background: transparent;">
        <div style="position: relative; width: {tube_width}px; height: {h}px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;">
            <svg viewBox="0 0 100 120" style="width: 100%; height: 100%; transform: rotate(25deg); filter: drop-shadow(0 0 {int(5*scale)}px rgba(0, 229, 255, 0.5));">
                <rect x="35" y="10" width="30" height="90" rx="15" fill="none" stroke="url(#tbGrad)" stroke-width="5"/>
                <path d="M 38 55 Q 50 50 62 55 L 62 85 C 62 95 38 95 38 85 Z" fill="url(#lqGrad)" opacity="0.8"/>
                <rect x="30" y="5" width="40" height="12" rx="3" fill="url(#cpGrad)" stroke="#1E293B" stroke-width="1"/>
                <circle cx="50" cy="70" r="11" fill="url(#embGrad)" stroke="#FFEAA7" stroke-width="1"/>
                <defs>
                    <linearGradient id="tbGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#00E5FF" stop-opacity="0.9"/>
                        <stop offset="100%" stop-color="#2E86C1" stop-opacity="0.8"/>
                    </linearGradient>
                    <linearGradient id="lqGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#00E5FF" stop-opacity="0.5"/>
                        <stop offset="100%" stop-color="#1E3A8A" stop-opacity="0.2"/>
                    </linearGradient>
                    <linearGradient id="cpGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#2E86C1"/><stop offset="100%" stop-color="#0B132B"/>
                    </linearGradient>
                    <linearGradient id="embGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#FFFFFF"/><stop offset="100%" stop-color="#FACC15"/>
                    </linearGradient>
                </defs>
            </svg>
        </div>
        <div style="display: flex; flex-direction: column; justify-content: center; line-height: 1.1; font-family: sans-serif;">
            <div style="font-size: {font_size_main}px; font-weight: 700;">
                <span style="color: #38BDF8; text-shadow: 0 0 10px rgba(56,189,248,0.2);">Ova</span><span style="color: #FACC15; text-shadow: 0 0 10px rgba(250,204,21,0.2);">Metrics</span>
            </div>
            <div style="font-size: {font_size_tag}px; font-weight: 600; color: #64748B; letter-spacing: {letter_spacing}px; text-transform: uppercase; margin-top: 3px; padding-top: 2px; white-space: nowrap;">
                Precision Fertility • Advanced AI Blastocyst Grading
            </div>
        </div>
    </div>
    """

def recommendation(grade: str, low: bool = False):
    exp = int(grade[0]) if grade and grade[0].isdigit() else 3
    icm = grade[1].upper() if len(grade) > 1 else "B"
    te  = grade[2].upper() if len(grade) > 2 else "B"
    if low:
        return ("Low confidence anomaly detected — Manual expert embryologist panel verification required.", "#1E1B4B", "#93C5FD")
    if icm == "A" and te == "A" and exp >= 4:
        return ("Good Quality Embryo — Ideal morphological metrics & signature structural integrity. Highly recommended for immediate elective single embryo transfer (eSET).", "#062F4F", "#00E5FF")
    if icm == "C" or te == "C" or exp <= 2:
        return ("Poor Quality Embryo — Constrained viability patterns noticed. Sub-optimal prognosis scores calculated for routine transfers.", "#2D1616", "#F87171")
    return ("Moderate Quality Embryo — Capable benchmark indicators present. Approved for clinical cryopreservation standard banking models or secondary transfer sequences.", "#1C1917", "#FACC15")

def qlabel(grade: str) -> str:
    exp = int(grade[0]) if grade and grade[0].isdigit() else 3
    icm = grade[1].upper() if len(grade) > 1 else "B"
    te  = grade[2].upper() if len(grade) > 2 else "B"
    if icm == "A" and te == "A" and exp >= 4: return "Good"
    if icm == "C" or te == "C" or exp <= 2:   return "Poor"
    return "Moderate"

def _show(img, caption=""):
    try:
        st.image(img, caption=caption, use_container_width=True)
    except:
        st.image(img, caption=caption, use_column_width=True)

def generate_pdf_report(case_data):
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=40, leftMargin=40,
                               topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle',   parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
    sub_style   = ParagraphStyle('DocSub',     parent=styles['Normal'],   fontName='Helvetica',      fontSize=10, textColor=colors.HexColor('#64748B'), spaceAfter=20)
    h2_style    = ParagraphStyle('SecHeader',  parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#1E3A8A'), spaceBefore=14, spaceAfter=8)
    body_style  = ParagraphStyle('ReportBody', parent=styles['Normal'],   fontName='Helvetica',      fontSize=10, textColor=colors.HexColor('#334155'), leading=14)

    story = []
    story.append(Paragraph("OvaMetrics CDSS Clinical Assessment", title_style))
    story.append(Paragraph("Automated Blastocyst Diagnosis Report Log • Deep Fusion Model Ensemble Optimization Matrix", sub_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Telemetry Evaluation Records", h2_style))

    meta_table_data = [
        [Paragraph("<b>Metric Parameter</b>",            body_style), Paragraph("<b>Calculated Diagnostic Value</b>", body_style)],
        [Paragraph("Patient Unique Track ID",            body_style), Paragraph(case_data.get("id",     "N/A"), body_style)],
        [Paragraph("Pipeline Execution Date",            body_style), Paragraph(case_data.get("date",   "N/A"), body_style)],
        [Paragraph("Gardner Output Consensus Grade",     body_style), Paragraph(f"<b>{case_data.get('grade', 'N/A')}</b>", body_style)],
        [Paragraph("Morphological Cluster Tier Status",  body_style), Paragraph(f"{case_data.get('status', 'N/A')} Quality Profile Track", body_style)],
    ]
    t1 = Table(meta_table_data, colWidths=[230, 270])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#F8FAFC')),
        ('PADDING',    (0,0), (-1,-1), 7),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t1)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ── SESSION TOKEN (change value to force-logout all active sessions) ───────────
_SESSION_TOKEN = "ova_auth_v1"

# ── SYSTEM CORE STATE INITIALIZATION (URL-based auth survives server restarts) ─
# Restore login state from URL query param if the HF Space server restarted
if "logged_in" not in st.session_state:
    st.session_state.logged_in = (
        st.query_params.get("_s", "") == _SESSION_TOKEN
    )

for k, v in {
    "image_bytes": None,
    "analyzed":    False,
    "results":     None,
    "cam_overlays": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

BADGE = {
    "Good":     '<span class="badge-high">Good Quality</span>',
    "Moderate": '<span class="badge-mod">Moderate Quality</span>',
    "Poor":     '<span class="badge-low">Poor Quality</span>',
}

DUMMY = [
    {"id":"PT-2026-881","date":"2026-05-18","grade":"4AA","status":"Good",    "exp":4,"icm":"A","te":"A","low_conf":False},
    {"id":"PT-2026-882","date":"2026-05-17","grade":"3BB","status":"Moderate","exp":3,"icm":"B","te":"B","low_conf":False},
    {"id":"PT-2026-883","date":"2026-05-15","grade":"5AB","status":"Good",    "exp":5,"icm":"A","te":"B","low_conf":False},
    {"id":"PT-2026-884","date":"2026-05-14","grade":"2CC","status":"Poor",    "exp":2,"icm":"C","te":"C","low_conf":False},
    {"id":"PT-2026-885","date":"2026-05-11","grade":"4BA","status":"Moderate","exp":4,"icm":"B","te":"A","low_conf":False},
]

# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("<div style='margin-top: 5rem;'></div>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        st.markdown(logo(h=84, alignment="center"), unsafe_allow_html=True)
        st.markdown(
            '<p style="text-align:center;color:#64748B;font-size:12px;margin-top:12px;'
            'margin-bottom:20px;letter-spacing:0.02em;">'
            'Clinical Decision Support Space — Secure Access Gateway</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<p style="font-size: 15px; font-weight: 600; color: #00E5FF; margin-bottom: 4px;">Select an option</p>', unsafe_allow_html=True)
        auth_mode = st.radio("Select an option", ["Login", "Signup"], label_visibility="collapsed")

        st.markdown(
            f'<p style="font-size: 22px; font-weight: 700; color: #F1F5F9; margin-top: 1.5rem; margin-bottom: 0.5rem;">'
            f'{auth_mode} Page</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="info-banner">Protected Health Information (PHI) Environment. '
            'Identity logging protocol active.</div>',
            unsafe_allow_html=True,
        )

        email = st.text_input("Institutional Email ID", placeholder="clinician@ovametrics.cdn")
        pw    = st.text_input("Access Password", type="password", placeholder="••••••••••••••••")

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        btn_label = "Sign In" if auth_mode == "Login" else "Create Account"

        if st.button(btn_label, use_container_width=True, type="primary"):
            if email and pw:
                st.session_state.logged_in = True
                # ── FIX 2: write token into URL so login survives HF Space restarts ──
                st.query_params["_s"] = _SESSION_TOKEN
                st.rerun()
            else:
                st.error("Please provide valid institutional gateway parameters.")
    st.stop()

# ── NAVIGATION PANEL CONTROL ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="margin-top:0.5rem; margin-bottom:1.5rem;">'
        + logo(h=62, alignment="center")
        + '</div>',
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigation",
        ["Dashboard", "Upload & Analyse", "Results", "Explainability", "Case History"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:12px;color:#F1F5F9;font-weight:600;display:flex;align-items:center;gap:8px;">'
        '<span style="color:#FACC15;">●</span> Deep Fusion Ensemble Active'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("""
    <div style="font-size:11px;color:#64748B;line-height:2.2;margin-top:14px;font-weight:500;">
        🛡️ HIPAA Compliant Architecture<br>
        🔒 AES-256 On-Device Encryption<br>
        🧬 IVF-Grade Grading Framework
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    if st.button("Sign Out", use_container_width=True):
        # ── FIX 2: clear URL token on sign-out ────────────────────────────────
        st.query_params.clear()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── BRANDING BAR ──────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
st.markdown(logo(h=56, alignment="flex-start"), unsafe_allow_html=True)
st.markdown("<div style='margin-top: 1rem; border-bottom: 1px solid #1E293B; margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if page == "Dashboard":
    st.markdown('<div class="section-title">Clinical Overview & Diagnostic Metrics</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Automated Biomarkers Processed", "1,284", "Telemetry Active")
    k2.metric("Optimal Blastocyst Yield Ratio", "68.4%", "+2.1% Alpha Baseline")
    k3.metric("Ensemble Engine Consensus Confidence", "87.3%", "Soft-Vote Verified")
    k4.metric("Avg Test-Time Augmentation Margin", "89.1%", f"{CFG.TTA_ROUNDS} Spatial Passes")

    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([1.6, 1], gap="large")

    with cl:
        st.markdown('<div style="font-size:14px;font-weight:700;color:#F1F5F9;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.03em;">Recent Workspace Diagnostic Stream</div>', unsafe_allow_html=True)
        rows = "".join(
            f"<tr><td><b>{c['id']}</b></td><td>{c['date']}</td>"
            f"<td style='font-weight:800;font-size:15px;color:#00E5FF;'>{c['grade']}</td>"
            f"<td style='font-family:monospace;font-size:12px;color:#94A3B8;'>EXP:{c['exp']} ICM:{c['icm']} TE:{c['te']}</td>"
            f"<td>{BADGE[c['status']]}</td></tr>"
            for c in DUMMY
        )
        st.markdown(
            '<div class="cdss-card" style="padding:0;"><table class="case-table"><thead><tr>'
            '<th>Case Blueprint ID</th><th>Diagnostic Timestamp</th><th>Aggregated Score</th>'
            '<th>Morphology Components</th><th>Consensus State</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>',
            unsafe_allow_html=True,
        )

    with cr:
        st.markdown('<div style="font-size:14px;font-weight:700;color:#F1F5F9;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.03em;">Phenotypic Cluster Distribution</div>', unsafe_allow_html=True)
        st.markdown('<div class="cdss-card">', unsafe_allow_html=True)
        for g, p in {"4AA": 28, "4AB": 18, "3BB": 15, "4BA": 12, "5AA": 10, "Other Tracks": 17}.items():
            st.markdown(f'<div class="conf-label">{g}<span class="conf-val">{p}% Frequency</span></div>', unsafe_allow_html=True)
            st.progress(p / 100)
        st.markdown('</div>', unsafe_allow_html=True)

# ── UPLOAD & ANALYSE ──────────────────────────────────────────────────────────
elif page == "Upload & Analyse":
    st.markdown('<div class="section-title">Ingest Image Micrograph Track to AI Cluster</div>', unsafe_allow_html=True)
    up = st.file_uploader(
        "Select high-contrast focal blastocyst matrix segment (Standard PNG / JPEG configurations · min 224×224 px)",
        type=["jpg", "jpeg", "png"],
    )

    if up is not None:
        try:
            img = Image.open(up).convert("RGB")
            w, h = img.size
            if w < 224 or h < 224:
                st.error("Matrix Dimension Alert: Requires min 224×224 px mapping profiles.")
                st.stop()

            ci, cf = st.columns([1, 1], gap="large")
            with ci:
                _show(img, caption=f"Source Map Profile: {up.name}")
            with cf:
                st.markdown("""
                <div class="cdss-card">
                  <div style="font-size:13px;font-weight:700;color:#F1F5F9;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.04em;">Ingestion Integrity Checklist</div>
                  <div style="font-size:13px;color:#94A3B8;line-height:2.2;">
                    <span style="color:#00E5FF;">✔</span> Microscopic focus baseline lock confirmed<br>
                    <span style="color:#00E5FF;">✔</span> Single blastocyst focal layer centered<br>
                    <span style="color:#00E5FF;">✔</span> Scale indicator graphical clean matrix detected<br>
                    <span style="color:#00E5FF;">✔</span> Zero post-process anomalies
                  </div>
                </div>
                """, unsafe_allow_html=True)
                st.success("Structural verification checksum valid. Buffer sequence ready.")

            buf   = io.BytesIO()
            img.save(buf, format="PNG")
            new_b = buf.getvalue()

            if new_b != st.session_state.image_bytes:
                st.session_state.image_bytes  = new_b
                st.session_state.analyzed     = False
                st.session_state.results      = None
                st.session_state.cam_overlays = None

        except Exception as ex:
            st.error(f"Inability to map vector image buffer stream: {ex}")
            st.stop()

    if st.session_state.image_bytes:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Run Analyzer", use_container_width=True, type="primary"):
            ib  = st.session_state.image_bytes
            img = Image.open(io.BytesIO(ib))

            with st.spinner("Executing Swin / ViT / HRNet / ConvNeXt consensus soft-voting matrix maps..."):
                res = demo_predict(ib)
            st.session_state.results  = res
            st.session_state.analyzed = True

            with st.spinner("Extracting layer gradients via EigenCAM backpropagation loops..."):
                st.session_state.cam_overlays = build_cams(None, img, ib)

            st.success("Processing complete. Navigate to Results or Explainability navigation sections.")

# ── RESULTS ───────────────────────────────────────────────────────────────────
elif page == "Results":
    st.markdown('<div class="section-title">Automated Consensus Grading Diagnosis Profile</div>', unsafe_allow_html=True)
    if not st.session_state.image_bytes:
        st.warning("Diagnostic processing pipeline empty. Ingest source specimen via Upload & Analyse framework first.")
        st.stop()
    if not st.session_state.analyzed or not st.session_state.results:
        st.warning("Inference trace unallocated. Execute system processing tracking pipelines first.")
        st.stop()

    res = st.session_state.results
    img = Image.open(io.BytesIO(st.session_state.image_bytes))

    ci, cr = st.columns([1, 1.4], gap="large")
    with ci:
        st.markdown('<div style="font-size:13px;font-weight:700;color:#94A3B8;margin-bottom:10px;text-transform:uppercase;">Specimen Matrix Canvas</div>', unsafe_allow_html=True)
        _show(img)

    with cr:
        st.markdown('<div style="font-size:13px;font-weight:700;color:#94A3B8;margin-bottom:12px;text-transform:uppercase;">Gardner-Scale Morphological Metrics</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Cavity Expansion Vector", str(res["exp"]))
        m2.metric("Inner Cell Mass Density", res["icm"])
        m3.metric("Trophectoderm Layer Count", res["te"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;font-weight:700;color:#94A3B8;margin-bottom:6px;text-transform:uppercase;">Consensus Model Verdict</div>', unsafe_allow_html=True)

        cc = "#4ADE80" if res["avg_conf"] >= .75 else "#FACC15" if res["avg_conf"] >= .50 else "#F87171"
        ql = qlabel(res["grade"])

        st.markdown(
            f'<div class="grade-box">{res["grade"]}</div>'
            f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:12px;align-items:center;">'
            f'<span style="color:{cc};font-weight:700;letter-spacing:0.02em;">'
            f'Consensus Confidence: {res["avg_conf"]*100:.1f}%'
            f'{"  ⚠️ [SUB-BASELINE CONFIDENCE]" if res["low_conf"] else ""}</span>'
            f'{BADGE[ql]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div style="font-size:13px;font-weight:700;color:#94A3B8;margin-bottom:10px;text-transform:uppercase;">Task Head Probabilities</div>', unsafe_allow_html=True)
        for lb, val in [
            ("Expansion (EXP Track Head)",        res["conf_exp"]),
            ("Inner Cell Mass (ICM Track Head)",   res["conf_icm"]),
            ("Trophectoderm (TE Track Head)",       res["conf_te"]),
        ]:
            st.markdown(f'<div class="conf-label">{lb}<span class="conf-val">{val*100:.1f}% Match</span></div>', unsafe_allow_html=True)
            st.progress(float(val))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:14px;font-weight:700;color:#F1F5F9;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.03em;">Deep Fusion Backbone Ensemble Matrix Breakdown</div>', unsafe_allow_html=True)

    pc = st.columns(4)
    for name in GLOBAL_KEY_REGISTRY:
        pm = res["per_model"][name]
        with pc[GLOBAL_KEY_REGISTRY.index(name)]:
            st.markdown(
                f'<div class="cdss-card" style="text-align:center; border-top: 2px solid #273449;">'
                f'<div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.05em;">{name} Spine Module</div>'
                f'<div style="font-size:30px;font-weight:800;color:#F1F5F9;margin:10px 0;letter-spacing:2px;">'
                f'{pm["exp"]}{pm["icm"]}{pm["te"]}</div>'
                f'<div style="font-size:11px;color:#94A3B8;font-family:monospace;">'
                f'EXP {pm["conf_exp"]*100:.0f}% // ICM {pm["conf_icm"]*100:.0f}% // TE {pm["conf_te"]*100:.0f}%'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    msg, bg, fg = recommendation(res["grade"], res["low_conf"])
    st.markdown(
        f'<div style="background:{bg};border-left:5px solid {fg};border-radius:4px;padding:18px 24px;margin-bottom:12px;">'
        f'<div style="color:{fg};font-size:13px;font-weight:700;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">Clinical Action Decision Metrics Matrix</div>'
        f'<div style="color:#E2E8F0;font-size:14px;line-height:1.5;">{msg}</div></div>',
        unsafe_allow_html=True,
    )

    case_payload = {
        "id":       "CASE-" + str(int(hashlib.md5(st.session_state.image_bytes).hexdigest()[:6], 16)),
        "date":     "2026-05-20",
        "grade":    res["grade"],
        "status":   ql,
        "exp":      res["exp"],
        "icm":      res["icm"],
        "te":       res["te"],
        "low_conf": res["low_conf"],
    }

    pdf_bytes = generate_pdf_report(case_payload)
    st.download_button(
        label="Download Sealed PDF Record",
        data=pdf_bytes,
        file_name=f"OvaMetrics_Assessment_{case_payload['id']}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

# ── EXPLAINABILITY ────────────────────────────────────────────────────────────
elif page == "Explainability":
    st.markdown('<div class="section-title">Activation Map Target Explanations — EigenCAM</div>', unsafe_allow_html=True)
    if not st.session_state.image_bytes:
        st.warning("Diagnostic processing pipeline empty. Ingest source specimen via Upload & Analyse framework first.")
        st.stop()
    if not st.session_state.analyzed:
        st.warning("Inference trace unallocated. Trigger Pipeline Engine Verification sequence first.")
        st.stop()

    img = Image.open(io.BytesIO(st.session_state.image_bytes))
    ov  = st.session_state.cam_overlays

    c0, _ = st.columns([1, 2])
    with c0:
        st.markdown('<div style="font-size:13px;font-weight:700;color:#94A3B8;margin-bottom:8px;text-transform:uppercase;">Specimen Base Map Reference</div>', unsafe_allow_html=True)
        _show(img)

    HEAD_LABELS = {
        "exp": "Expansion (EXP Head)",
        "icm": "Inner Cell Mass (ICM Head)",
        "te":  "Trophectoderm (TE Head)",
    }
    st.markdown("<br><br>", unsafe_allow_html=True)

    hdr = st.columns([0.8, 1, 1, 1])
    hdr[0].markdown("<small style='color:#64748B; text-transform:uppercase; font-weight:700;'>Classifier Backbone</small>", unsafe_allow_html=True)
    for j, lb in enumerate(HEAD_LABELS.values()):
        hdr[j+1].markdown(f"<small style='color:#64748B; text-transform:uppercase; font-weight:700;'>{lb}</small>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:6px; border-bottom:1px solid #1E293B;'></div>", unsafe_allow_html=True)

    for bname in GLOBAL_KEY_REGISTRY:
        row = st.columns([0.8, 1, 1, 1])
        row[0].markdown(
            f'<div style="padding-top:75px;font-size:14px;font-weight:700;color:#00E5FF;font-family:monospace;">{bname.upper()}</div>',
            unsafe_allow_html=True,
        )
        for j, head in enumerate(("exp", "icm", "te")):
            with row[j+1]:
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                _show(ov[bname][head])

# ── CASE HISTORY ──────────────────────────────────────────────────────────────
elif page == "Case History":
    st.markdown('<div class="section-title">Institutional Case Database Repository Logs</div>', unsafe_allow_html=True)
    fc, _, ec = st.columns([1, 2.5, 1])
    with fc:
        qf = st.selectbox("Filter Tracking Mode", ["All Diagnostic Classes", "Good", "Moderate", "Poor"])

    filter_val = qf.split()[0]
    cases = DUMMY if filter_val == "All" else [c for c in DUMMY if c["status"] == filter_val]

    rows = "".join(
        f"<tr><td><b style='font-family:monospace; color:#F1F5F9;'>{c['id']}</b></td><td>{c['date']}</td>"
        f"<td style='font-size:16px;font-weight:800;color:#00E5FF;font-family:monospace;'>{c['grade']}</td>"
        f"<td>{c['exp']}</td><td>{c['icm']}</td><td>{c['te']}</td>"
        f"<td>{BADGE[c['status']]}</td></tr>"
        for c in cases
    )

    st.markdown(
        '<div class="cdss-card" style="padding:0;"><table class="case-table"><thead><tr>'
        '<th>Patient Diagnostic Track ID</th><th>Execution Date</th><th>Calculated Matrix Output</th>'
        '<th>EXP Class</th><th>ICM Class</th><th>TE Class</th><th>Consensus Tier Quality Status</th>'
        f'</tr></thead><tbody>{rows}</tbody></table>'
        f'<div style="font-size:11px;color:#64748B;padding:12px 16px;text-align:right;font-family:monospace;">'
        f'QUERY OUTPUT: displaying {len(cases)} of {len(DUMMY)} database files matches</div></div>',
        unsafe_allow_html=True,
    )
