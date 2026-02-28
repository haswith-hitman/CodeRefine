"""
CodeRefine — Smarter Code. Cleaner Future.
Run: python -m streamlit run app.py
"""

import streamlit as st
import sys, os, json, re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import (
    init_db, create_user, authenticate_user,
    save_review, get_user_history, get_user_stats,
    get_language_breakdown, get_recent_trend,
    update_user_settings,
    save_snippet, get_snippets, get_snippet, update_snippet,
    toggle_snippet_favorite, delete_snippet,
    save_challenge_attempt, get_challenge_stats,
    complexity_to_score,
)

st.set_page_config(
    page_title="CodeRefine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── Session defaults ──────────────────────────────────────────────────────────
_DEFAULTS = {
    "user": None, "page": "login", "api_key": "",
    "login_error": None, "signup_error": None, "signup_success": False,
    "review_result": None, "review_language": "Python", "review_code": "",
    "rw_result": None, "rw_language": "Python",
    "cx_score": None, "cf_score": None,
    "explain_result": None, "translate_result": None,
    "current_challenge": None, "challenge_eval": None,
    "snippet_edit_id": None, "show_solution": False,
    "ide_code": "", "ide_lang": "Python",
    "theme": "dark", "accent": "indigo",
    "timeline_result": None, "timeline_era": "2010", "timeline_lang": "Python",
    "dna_result": None, "dna_lang": "Python",
    "interview_code": "", "interview_lang": "Python", "interview_history": [],
    "interview_current": None, "interview_done": False, "interview_answer": "",
    "interview_scores": [],
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C", "C#",
    "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R",
    "MATLAB", "Bash", "SQL", "HTML/CSS",
]

ACCENT_COLORS = {
    "indigo":  {"p1": "#6366F1", "p2": "#8B5CF6", "glow": "rgba(99,102,241,0.22)"},
    "cyan":    {"p1": "#06B6D4", "p2": "#0891B2", "glow": "rgba(6,182,212,0.22)"},
    "emerald": {"p1": "#10B981", "p2": "#059669", "glow": "rgba(16,185,129,0.22)"},
    "rose":    {"p1": "#F43F5E", "p2": "#E11D48", "glow": "rgba(244,63,94,0.22)"},
    "amber":   {"p1": "#F59E0B", "p2": "#D97706", "glow": "rgba(245,158,11,0.22)"},
}

# ── Theme definitions ─────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg": "#060910", "sf": "#0D1323", "sf2": "#0F172A",
        "bd": "rgba(99,102,241,0.14)", "tx": "#E2E8F0", "mt": "#64748B",
        "tx2": "#CBD5E1", "inp_bg": "#07090F", "sidebar_bg": "#07101E",
        "code_bg": "#050810", "code_tx": "#E2E8F0",
        "is_light": False,
    },
    "midnight": {
        "bg": "#020408", "sf": "#060C18", "sf2": "#0A1020",
        "bd": "rgba(99,102,241,0.10)", "tx": "#CBD5E1", "mt": "#475569",
        "tx2": "#94A3B8", "inp_bg": "#030610", "sidebar_bg": "#040A15",
        "code_bg": "#020408", "code_tx": "#CBD5E1",
        "is_light": False,
    },
    "slate": {
        "bg": "#0F172A", "sf": "#1E293B", "sf2": "#243348",
        "bd": "rgba(148,163,184,0.18)", "tx": "#F1F5F9", "mt": "#94A3B8",
        "tx2": "#CBD5E1", "inp_bg": "#0D1526", "sidebar_bg": "#0B1220",
        "code_bg": "#0D1526", "code_tx": "#F1F5F9",
        "is_light": False,
    },
    "light": {
        "bg": "#F8FAFC", "sf": "#FFFFFF", "sf2": "#F1F5F9",
        "bd": "rgba(99,102,241,0.20)", "tx": "#1E293B", "mt": "#64748B",
        "tx2": "#475569", "inp_bg": "#FFFFFF", "sidebar_bg": "#F1F5F9",
        "code_bg": "#F8FAFC", "code_tx": "#1E293B",
        "is_light": True,
    },
    "warm": {
        "bg": "#FEFCE8", "sf": "#FFFFFF", "sf2": "#FEF9C3",
        "bd": "rgba(245,158,11,0.25)", "tx": "#1C1917", "mt": "#78716C",
        "tx2": "#44403C", "inp_bg": "#FFFFFF", "sidebar_bg": "#FEF3C7",
        "code_bg": "#FFFBEB", "code_tx": "#1C1917",
        "is_light": True,
    },
}

# ════════════════════════════════════════════════════════════════════════════════
#  CSS
# ════════════════════════════════════════════════════════════════════════════════
def inject_css():
    ac  = ACCENT_COLORS.get(st.session_state.accent, ACCENT_COLORS["indigo"])
    th  = THEMES.get(st.session_state.theme, THEMES["dark"])
    p1, p2, glow = ac["p1"], ac["p2"], ac["glow"]
    bg, sf, sf2, bd = th["bg"], th["sf"], th["sf2"], th["bd"]
    tx, mt, tx2     = th["tx"], th["mt"], th["tx2"]
    inp_bg, sb_bg   = th["inp_bg"], th["sidebar_bg"]
    code_bg, code_tx = th["code_bg"], th["code_tx"]
    is_light        = th["is_light"]

    # Dynamic values for light vs dark
    shadow  = "0 4px 20px rgba(0,0,0,0.08)" if is_light else "0 4px 20px rgba(0,0,0,0.5)"
    grid_c  = "rgba(99,102,241,0.04)"        if is_light else "rgba(99,102,241,0.018)"
    sb_tx   = "#374151"   if is_light else "#7A8BA8"
    sb_tx_a = "#1E293B"   if is_light else "#A5B4FC"
    exp_bg  = sf2
    exp_sum = sf
    hist_bg = f"rgba(99,102,241,{'0.06' if is_light else '0.07'})"
    hist_bd = f"rgba(99,102,241,{'0.18' if is_light else '0.16'})"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

:root {{
  --p1:{p1}; --p2:{p2}; --glow:{glow};
  --bg:{bg}; --sf:{sf}; --sf2:{sf2}; --bd:{bd};
  --tx:{tx}; --mt:{mt}; --tx2:{tx2};
  --inp-bg:{inp_bg}; --sb-bg:{sb_bg};
  --code-bg:{code_bg}; --code-tx:{code_tx};
  --shadow:{shadow};
}}

*,*::before,*::after {{ font-family:'Outfit',sans-serif !important; box-sizing:border-box; }}
code,pre,.stCode,.stTextArea textarea {{ font-family:'JetBrains Mono',monospace !important; }}

/* Hide Streamlit chrome */
#MainMenu,footer,header {{ visibility:hidden; }}
.stDeployButton {{ display:none; }}
[data-testid="stSidebarNav"] {{ display:none; }}
button[title="View fullscreen"] {{ display:none; }}

/* ── BASE BACKGROUNDS ── */
html,body,.stApp {{ background:var(--bg) !important; color:var(--tx) !important; min-height:100vh; }}
.stApp > div,.main,.main > div,.block-container,
[data-testid="stAppViewContainer"],[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"] {{ background:transparent !important; }}
[data-testid="stHorizontalBlock"] > div {{ background:transparent !important; }}
[data-testid="stMetric"] {{ background:transparent !important; }}
div[data-testid="column"] > div > div > div {{ background:transparent !important; }}

/* Grid background */
.stApp::before {{
  content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:
    linear-gradient({grid_c} 1px, transparent 1px),
    linear-gradient(90deg,{grid_c} 1px, transparent 1px);
  background-size:52px 52px;
}}

/* ── TEXT CURSOR — always visible ── */
.stTextArea textarea,
.stTextInput input,
input, textarea {{
  caret-color: {p1} !important;
  caret-width: 2px !important;
}}
/* Make selection visible */
.stTextArea textarea::selection,
.stTextInput input::selection,
textarea::selection, input::selection {{
  background: {p1}40 !important;
  color: var(--tx) !important;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
  background:var(--sb-bg) !important;
  border-right:1px solid var(--bd) !important;
  min-width:230px !important;
}}
[data-testid="stSidebar"] .block-container {{ padding:1.2rem 0.85rem !important; }}
.sb-brand {{
  font-size:1.3rem; font-weight:900; letter-spacing:-0.5px;
  background:linear-gradient(135deg,var(--p1),var(--p2),#06B6D4);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}}
.sb-tag {{ font-size:0.57rem; color:var(--mt); letter-spacing:2.5px; text-transform:uppercase; margin-bottom:0.9rem; }}
.sb-div {{ height:1px; background:var(--bd); margin:0.6rem 0; }}
.sb-sec {{ font-size:0.57rem; color:var(--mt); letter-spacing:2.5px; text-transform:uppercase; margin:0.8rem 0 0.45rem; padding:0 0.3rem; font-weight:700; }}
.user-chip {{
  display:flex; align-items:center; gap:0.55rem;
  background:rgba(99,102,241,0.10); border:1px solid rgba(99,102,241,0.22);
  border-radius:11px; padding:0.6rem 0.75rem; margin-bottom:0.85rem;
}}
.u-av {{
  width:28px; height:28px;
  background:linear-gradient(135deg,var(--p1),var(--p2));
  border-radius:7px; display:flex; align-items:center; justify-content:center;
  font-size:0.8rem; font-weight:800; color:white; flex-shrink:0;
}}
.u-name {{ font-size:0.78rem; font-weight:700; color:var(--tx); line-height:1.2; }}
.u-role {{ font-size:0.62rem; color:#10B981; }}

/* ── NAV RADIO ── */
.stRadio > div {{ gap:0.15rem !important; flex-direction:column !important; }}
.stRadio > div > label {{
  background:transparent !important; border:1px solid transparent !important;
  border-radius:9px !important; padding:0.5rem 0.72rem !important;
  color:{sb_tx} !important; font-size:0.83rem !important; font-weight:600 !important;
  transition:all 0.14s !important; width:100% !important; cursor:pointer !important;
  display:flex !important; align-items:center !important;
}}
.stRadio > div > label:hover {{
  background:rgba(99,102,241,0.09) !important;
  color:{sb_tx_a} !important;
  border-color:rgba(99,102,241,0.15) !important;
}}
.stRadio > div > label:has(input:checked) {{
  background:rgba(99,102,241,0.15) !important;
  border-color:rgba(99,102,241,0.32) !important;
  color:{sb_tx_a} !important;
}}
/* Hide the actual radio circle */
.stRadio > div > label > div:first-child {{ display:none !important; }}
/* Ensure label text is visible */
.stRadio > div > label > div {{ color:inherit !important; }}
.stRadio > div > label > div > p {{
  color:inherit !important; font-size:0.83rem !important;
  font-weight:600 !important; margin:0 !important;
}}

/* ── AUTH ── */
.brand-logo {{
  font-size:2.8rem; font-weight:900; letter-spacing:-2px; display:block;
  background:linear-gradient(135deg,var(--p1) 0%,var(--p2) 50%,#06B6D4 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}}
.brand-tag {{ color:var(--mt); font-size:0.67rem; letter-spacing:3.5px; text-transform:uppercase; margin-top:0.4rem; }}
.pill {{
  background:rgba(99,102,241,0.09); border:1px solid rgba(99,102,241,0.22);
  border-radius:20px; padding:0.25rem 0.75rem; font-size:0.72rem;
  color:var(--p1); display:inline-block; margin:0.2rem;
}}
.auth-card {{
  background:var(--sf); border:1px solid var(--bd); border-radius:20px;
  padding:2rem 2.2rem; box-shadow:var(--shadow);
}}
.card-title {{ font-size:1.5rem; font-weight:800; color:var(--tx); margin-bottom:0.15rem; }}
.card-sub {{ color:var(--mt); font-size:0.82rem; margin-bottom:1.4rem; }}
.msg-ok  {{ background:rgba(16,185,129,0.09);  border:1px solid rgba(16,185,129,0.28); border-radius:9px; padding:0.6rem 0.9rem; color:#10B981; font-size:0.81rem; margin-bottom:0.9rem; }}
.msg-err {{ background:rgba(239,68,68,0.09);   border:1px solid rgba(239,68,68,0.28);  border-radius:9px; padding:0.6rem 0.9rem; color:#EF4444; font-size:0.81rem; margin-bottom:0.9rem; }}
.msg-warn{{ background:rgba(245,158,11,0.09);  border:1px solid rgba(245,158,11,0.28); border-radius:9px; padding:0.6rem 0.9rem; color:#F59E0B; font-size:0.81rem; margin-bottom:0.9rem; }}
.divider {{ display:flex; align-items:center; margin:1.2rem 0; color:var(--mt); font-size:0.76rem; }}
.divider::before,.divider::after {{ content:''; flex:1; height:1px; background:var(--bd); }}
.divider::before {{ margin-right:1rem; }} .divider::after {{ margin-left:1rem; }}

/* ── PAGE TITLE ── */
.pg-title {{ font-size:1.75rem; font-weight:800; letter-spacing:-0.5px; color:var(--tx); margin-bottom:0.12rem; }}
.pg-sub   {{ color:var(--mt); font-size:0.84rem; margin-bottom:1.3rem; }}

/* ── PANELS ── */
.panel {{
  background:var(--sf); border:1px solid var(--bd);
  border-radius:14px; padding:1.2rem; margin-bottom:0.9rem;
  box-shadow:var(--shadow);
}}
.panel-hdr {{ font-size:0.63rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:0.75rem; color:var(--p1); }}

/* ── SUMMARY BOX ── */
.summary-box {{
  background:var(--sf2); border:1px solid var(--bd);
  border-left:3px solid var(--p1); border-radius:10px;
  padding:1rem 1.2rem; margin-bottom:1.1rem;
}}
.summary-label {{ font-size:0.62rem; font-weight:700; letter-spacing:2px; color:var(--p1); text-transform:uppercase; margin-bottom:0.38rem; }}
.summary-text {{ font-size:0.86rem; color:var(--tx2); line-height:1.72; }}

/* ── REVIEW RESULT SECTIONS ── */
.rv {{ border-radius:12px; padding:0.9rem 1.1rem; margin-bottom:0.65rem; border:1px solid; }}
.rv-bugs {{ background:{'rgba(239,68,68,0.05)' if not is_light else 'rgba(239,68,68,0.04)'}; border-color:rgba(239,68,68,0.22); }}
.rv-perf {{ background:{'rgba(245,158,11,0.05)' if not is_light else 'rgba(245,158,11,0.04)'}; border-color:rgba(245,158,11,0.22); }}
.rv-sec  {{ background:{'rgba(16,185,129,0.05)' if not is_light else 'rgba(16,185,129,0.04)'}; border-color:rgba(16,185,129,0.22); }}
.rv-best {{ background:{'rgba(99,102,241,0.05)' if not is_light else 'rgba(99,102,241,0.04)'}; border-color:rgba(99,102,241,0.22); }}
.rv-hdr  {{ font-size:0.87rem; font-weight:700; margin-bottom:0.55rem; display:flex; align-items:center; gap:0.4rem; }}
.rv-bugs .rv-hdr {{ color:#EF4444; }} .rv-perf .rv-hdr {{ color:#F59E0B; }}
.rv-sec  .rv-hdr {{ color:#10B981; }} .rv-best .rv-hdr {{ color:#818CF8; }}
.rv-item {{ padding:0.48rem 0; border-bottom:1px solid var(--bd); }}
.rv-item:last-child {{ border-bottom:none; }}
.rv-item-title {{ font-size:0.84rem; font-weight:700; color:var(--tx); margin-bottom:0.13rem; display:flex; align-items:center; gap:0.45rem; flex-wrap:wrap; }}
.rv-item-desc  {{ font-size:0.79rem; color:var(--tx2); line-height:1.55; }}
.rv-item-fix   {{ font-size:0.76rem; color:{'#1d4ed8' if is_light else '#7DD3FC'}; background:{'rgba(29,78,216,0.06)' if is_light else 'rgba(6,182,212,0.07)'}; border:1px solid {'rgba(29,78,216,0.15)' if is_light else 'rgba(6,182,212,0.18)'}; border-radius:6px; padding:0.32rem 0.6rem; margin-top:0.22rem; font-family:'JetBrains Mono',monospace !important; }}
.rv-item-meta  {{ font-size:0.71rem; margin-top:0.14rem; color:var(--mt); }}
.sev-critical {{ background:rgba(239,68,68,0.12);  color:#EF4444; border-radius:4px; padding:0.05rem 0.38rem; font-size:0.62rem; font-weight:700; }}
.sev-high     {{ background:rgba(249,115,22,0.12); color:#F97316; border-radius:4px; padding:0.05rem 0.38rem; font-size:0.62rem; font-weight:700; }}
.sev-medium   {{ background:rgba(245,158,11,0.12); color:#F59E0B; border-radius:4px; padding:0.05rem 0.38rem; font-size:0.62rem; font-weight:700; }}
.sev-low      {{ background:rgba(99,102,241,0.12); color:#818CF8; border-radius:4px; padding:0.05rem 0.38rem; font-size:0.62rem; font-weight:700; }}

/* ── SCORE / COMPLEXITY ── */
.score-grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.55rem; margin-bottom:0.75rem; }}
.score-item {{ text-align:center; background:var(--sf2); border:1px solid var(--bd); border-radius:10px; padding:0.65rem 0.4rem; }}
.score-val  {{ font-size:1.35rem; font-weight:800; line-height:1; margin-bottom:0.16rem; }}
.score-lbl  {{ font-size:0.61rem; color:var(--mt); text-transform:uppercase; letter-spacing:1px; }}
.cx-bar  {{ background:{'rgba(0,0,0,0.08)' if is_light else 'rgba(255,255,255,0.06)'}; border-radius:6px; height:7px; overflow:hidden; margin:0.28rem 0 0.55rem; }}
.cx-fill {{ height:100%; border-radius:6px; transition:width 0.5s ease; }}
.char-cnt {{ font-size:0.65rem; color:var(--mt); text-align:right; font-family:'JetBrains Mono',monospace !important; margin-top:0.2rem; }}
.char-cnt.warn {{ color:#F59E0B; }} .char-cnt.danger {{ color:#EF4444; }}

/* ── VERDICT ── */
.verdict-excellent {{ color:#10B981; background:rgba(16,185,129,0.10); border:1px solid rgba(16,185,129,0.28); border-radius:7px; padding:0.28rem 0.75rem; font-size:0.74rem; font-weight:700; display:inline-block; }}
.verdict-good      {{ color:#06B6D4; background:rgba(6,182,212,0.10);  border:1px solid rgba(6,182,212,0.28);  border-radius:7px; padding:0.28rem 0.75rem; font-size:0.74rem; font-weight:700; display:inline-block; }}
.verdict-needs_work{{ color:#F59E0B; background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.28); border-radius:7px; padding:0.28rem 0.75rem; font-size:0.74rem; font-weight:700; display:inline-block; }}
.verdict-poor      {{ color:#EF4444; background:rgba(239,68,68,0.10);  border:1px solid rgba(239,68,68,0.28);  border-radius:7px; padding:0.28rem 0.75rem; font-size:0.74rem; font-weight:700; display:inline-block; }}

/* ── IMPROVEMENT CARDS ── */
.imp-card {{ background:var(--sf2); border:1px solid var(--bd); border-radius:11px; padding:0.85rem 1rem; margin-bottom:0.55rem; }}
.imp-cat  {{ font-size:0.62rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:0.25rem; }}
.imp-cat.Performance {{ color:#F59E0B; }} .imp-cat.Security   {{ color:#10B981; }}
.imp-cat.Readability {{ color:#818CF8; }} .imp-cat.Bug_Fix    {{ color:#EF4444; }}
.imp-cat.Best_Practice {{ color:#06B6D4; }}
.imp-title  {{ font-size:0.84rem; font-weight:700; color:var(--tx); margin-bottom:0.18rem; }}
.imp-desc   {{ font-size:0.78rem; color:var(--tx2); line-height:1.55; }}
.imp-impact {{ font-size:0.72rem; color:var(--mt); margin-top:0.2rem; font-style:italic; }}

/* ── IDE / CODE EDITOR ── */
.ide-wrap {{
  border:1px solid var(--bd); border-radius:12px; overflow:hidden;
  box-shadow:var(--shadow);
}}
.ide-topbar {{
  background:var(--sf); border-bottom:1px solid var(--bd);
  padding:0.45rem 0.9rem; display:flex; align-items:center; gap:0.45rem;
}}
.ide-dot-r {{ width:11px; height:11px; border-radius:50%; background:#FF5F57; }}
.ide-dot-y {{ width:11px; height:11px; border-radius:50%; background:#FFBD2E; }}
.ide-dot-g {{ width:11px; height:11px; border-radius:50%; background:#28CA41; }}
.ide-lang-tag {{
  margin-left:auto; font-size:0.62rem; font-weight:700; letter-spacing:1.5px;
  text-transform:uppercase; color:var(--mt);
  background:var(--sf2); border:1px solid var(--bd);
  border-radius:5px; padding:0.15rem 0.5rem;
}}
/* Code textarea styled as IDE */
.stTextArea textarea {{
  background:var(--code-bg) !important;
  color:var(--code-tx) !important;
  border:none !important;
  border-radius:0 !important;
  font-family:'JetBrains Mono',monospace !important;
  font-size:0.84rem !important;
  line-height:1.7 !important;
  padding:1rem !important;
  tab-size:4 !important;
  caret-color:{p1} !important;
  resize:vertical !important;
}}
.stTextArea textarea:focus {{
  border:none !important;
  box-shadow:inset 0 0 0 2px {p1}50 !important;
  outline:none !important;
}}
.stTextArea label {{
  color:var(--mt) !important; font-size:0.68rem !important;
  font-weight:700 !important; letter-spacing:1px !important;
  text-transform:uppercase !important;
}}

/* ── INPUTS ── */
.stTextInput > div > div > input {{
  background:var(--inp-bg) !important; border:1px solid var(--bd) !important;
  border-radius:9px !important; color:var(--tx) !important;
  padding:0.62rem 0.85rem !important;
  caret-color:{p1} !important;
}}
.stTextInput > div > div > input::placeholder {{ color:var(--mt) !important; opacity:0.7; }}
.stTextInput > div > div > input:focus {{
  border-color:var(--p1) !important;
  box-shadow:0 0 0 3px var(--glow) !important;
}}
.stTextInput label {{ color:var(--mt) !important; font-size:0.68rem !important; font-weight:700 !important; letter-spacing:1px !important; text-transform:uppercase !important; }}

/* ── SELECTBOX ── */
.stSelectbox > div > div {{
  background:var(--inp-bg) !important; border:1px solid var(--bd) !important;
  border-radius:9px !important; color:var(--tx) !important;
}}
.stSelectbox > div > div > div {{ color:var(--tx) !important; }}
.stSelectbox label {{ color:var(--mt) !important; font-size:0.68rem !important; font-weight:700 !important; letter-spacing:1px !important; text-transform:uppercase !important; }}

/* ── BUTTONS ── */
.stButton > button {{
  border-radius:9px !important; font-family:'Outfit',sans-serif !important;
  font-weight:700 !important; transition:all 0.18s ease !important;
  border:none !important;
  background:linear-gradient(135deg,var(--p1),var(--p2)) !important;
  color:white !important;
  box-shadow:0 3px 12px var(--glow) !important;
}}
.stButton > button:hover {{
  transform:translateY(-1px) !important;
  box-shadow:0 6px 18px var(--glow) !important;
}}
/* Sidebar sign out */
[data-testid="stSidebar"] .stButton > button {{
  background:rgba(239,68,68,0.08) !important;
  border:1px solid rgba(239,68,68,0.25) !important;
  color:#EF4444 !important; box-shadow:none !important;
  font-size:0.78rem !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
  background:rgba(239,68,68,0.16) !important; transform:none !important;
}}
/* Download button */
.stDownloadButton > button {{
  background:var(--sf2) !important; border:1px solid var(--bd) !important;
  color:var(--p1) !important; box-shadow:none !important; font-size:0.78rem !important;
}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
  background:transparent !important; gap:0.3rem !important;
  border-bottom:1px solid var(--bd) !important;
}}
.stTabs [data-baseweb="tab"] {{
  background:transparent !important; border:none !important;
  color:var(--mt) !important; font-weight:600 !important;
  font-size:0.82rem !important; padding:0.42rem 0.85rem !important;
  border-radius:7px 7px 0 0 !important;
}}
.stTabs [aria-selected="true"] {{
  background:rgba(99,102,241,0.10) !important;
  color:var(--p1) !important;
  border-bottom:2px solid var(--p1) !important;
}}

/* ── EXPANDER ── */
[data-testid="stExpander"] details {{
  background:{exp_bg} !important; border:1px solid var(--bd) !important;
  border-radius:11px !important;
}}
[data-testid="stExpander"] details summary {{
  background:{exp_sum} !important; border-radius:9px !important;
  color:var(--tx) !important; font-weight:700 !important;
  padding:0.62rem 0.95rem !important;
}}
[data-testid="stExpander"] details summary:hover {{ color:var(--p1) !important; }}
[data-testid="stExpander"] details summary > span {{ color:var(--tx) !important; }}

/* ── METRICS ── */
.stat-card {{
  background:var(--sf); border:1px solid var(--bd); border-radius:13px;
  padding:1rem; position:relative; overflow:hidden;
  box-shadow:var(--shadow);
}}
.stat-card::after {{
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background:var(--c-grad); border-radius:13px 13px 0 0;
}}
.stat-icon  {{ font-size:1.1rem; margin-bottom:0.38rem; }}
.stat-val   {{ font-size:1.6rem; font-weight:800; color:var(--tx); line-height:1; margin-bottom:0.14rem; }}
.stat-label {{ font-size:0.63rem; color:var(--mt); text-transform:uppercase; letter-spacing:1px; }}

/* ── SNIPPET CARD ── */
.snippet-card {{
  background:var(--sf); border:1px solid var(--bd); border-radius:13px;
  padding:1rem 1.1rem; margin-bottom:0.65rem; transition:border-color 0.18s;
  box-shadow:var(--shadow);
}}
.snippet-card:hover {{ border-color:var(--p1); }}
.snippet-title {{ font-size:0.9rem; font-weight:700; color:var(--tx); margin-bottom:0.15rem; display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap; }}
.snippet-desc  {{ font-size:0.76rem; color:var(--mt); margin-bottom:0.38rem; }}
.snippet-preview {{
  font-family:'JetBrains Mono',monospace !important; font-size:0.71rem;
  color:var(--tx2); background:var(--code-bg); border:1px solid var(--bd);
  border-radius:6px; padding:0.38rem 0.6rem; white-space:pre; overflow:hidden;
  text-overflow:ellipsis; margin-bottom:0.45rem; max-height:48px;
}}
.snippet-meta {{ font-size:0.65rem; color:var(--mt); display:flex; align-items:center; gap:0.55rem; flex-wrap:wrap; }}
.lang-badge {{ background:rgba(99,102,241,0.15); color:var(--p1); border-radius:4px; padding:0.04rem 0.38rem; font-size:0.64rem; font-weight:700; }}
.tag-badge  {{ background:rgba(6,182,212,0.10); color:#06B6D4; border-radius:4px; padding:0.04rem 0.38rem; font-size:0.62rem; }}

/* ── CHALLENGE CARD ── */
.challenge-card {{
  background:var(--sf); border:1px solid var(--bd);
  border-radius:14px; padding:1.2rem 1.3rem; margin-bottom:0.75rem;
  box-shadow:var(--shadow);
}}
.diff-easy   {{ color:#10B981; background:rgba(16,185,129,0.10); border:1px solid rgba(16,185,129,0.28); }}
.diff-medium {{ color:#F59E0B; background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.28); }}
.diff-hard   {{ color:#EF4444; background:rgba(239,68,68,0.10);  border:1px solid rgba(239,68,68,0.28); }}
.diff-badge  {{ border-radius:6px; padding:0.1rem 0.48rem; font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; display:inline-block; }}

/* ── HISTORY ITEMS ── */
.hist-item  {{ background:{hist_bg}; border:1px solid {hist_bd}; border-radius:8px; padding:0.52rem 0.72rem; margin-bottom:0.32rem; }}
.hist-snip  {{ color:var(--mt); font-family:'JetBrains Mono',monospace !important; font-size:0.65rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.hist-meta  {{ color:var(--mt); font-size:0.6rem; margin-top:0.16rem; opacity:0.8; }}

/* ── PROGRESS BAR ── */
.stProgress > div > div > div > div {{
  background:linear-gradient(90deg,var(--p1),var(--p2)) !important;
  border-radius:6px !important;
}}

/* ── THEME PICKER SWATCHES ── */
.swatch-row {{ display:flex; gap:0.6rem; flex-wrap:wrap; margin:0.5rem 0 1rem; }}
.swatch {{
  width:36px; height:36px; border-radius:8px; cursor:pointer;
  border:3px solid transparent; transition:all 0.15s;
  display:inline-flex; align-items:center; justify-content:center;
  font-size:0.7rem; font-weight:700;
}}
.swatch:hover {{ transform:scale(1.1); }}
.swatch.active {{ border-color:var(--p1) !important; box-shadow:0 0 0 2px var(--glow); }}

/* ── TIMELINE ── */
.tl-header {{
  text-align:center; padding:1.5rem 0 0.5rem;
}}
.tl-era-pill {{
  display:inline-flex; align-items:center; gap:0.45rem;
  background:linear-gradient(135deg,var(--p1),var(--p2));
  color:white; border-radius:24px; padding:0.38rem 1.1rem;
  font-size:0.82rem; font-weight:700; margin-bottom:1rem;
  box-shadow:0 4px 18px var(--glow);
}}
.tl-slider-container {{
  background:var(--sf); border:1px solid var(--bd);
  border-radius:16px; padding:1.2rem 1.5rem; margin-bottom:1rem;
}}
.tl-era-grid {{
  display:flex; gap:0.5rem; flex-wrap:wrap; margin:0.75rem 0 0.5rem;
}}
.tl-era-btn {{
  display:flex; flex-direction:column; align-items:center;
  background:var(--sf2); border:1.5px solid var(--bd);
  border-radius:12px; padding:0.55rem 0.7rem; cursor:pointer;
  font-size:0.72rem; font-weight:600; color:var(--mt);
  transition:all 0.15s; flex:1; min-width:70px;
}}
.tl-era-btn:hover {{ border-color:var(--p1); color:var(--tx); }}
.tl-era-btn.active {{
  border-color:var(--p1); background:rgba(99,102,241,0.14);
  color:var(--p1); box-shadow:0 0 0 2px var(--glow);
}}
.tl-era-icon {{ font-size:1.3rem; margin-bottom:0.2rem; }}
.tl-era-year {{ font-size:0.65rem; font-weight:800; }}
.tl-era-label {{ font-size:0.58rem; opacity:0.75; }}
.tl-result-header {{
  display:flex; align-items:center; gap:0.8rem;
  padding:0.9rem 1.1rem; background:var(--sf2);
  border-radius:12px; margin-bottom:0.75rem;
  border:1px solid var(--bd);
}}
.tl-era-big-icon {{ font-size:2rem; }}
.tl-era-title {{ font-size:1rem; font-weight:800; color:var(--tx); }}
.tl-era-subtitle {{ font-size:0.75rem; color:var(--mt); }}
.tl-score-row {{
  display:flex; gap:0.7rem; margin-bottom:0.9rem; flex-wrap:wrap;
}}
.tl-score-card {{
  flex:1; min-width:110px;
  background:var(--sf); border:1px solid var(--bd);
  border-radius:10px; padding:0.65rem 0.9rem; text-align:center;
}}
.tl-score-val {{ font-size:1.4rem; font-weight:800; color:var(--p1); }}
.tl-score-label {{ font-size:0.62rem; color:var(--mt); text-transform:uppercase; letter-spacing:1.5px; }}
.tl-change-item {{
  background:var(--sf); border:1px solid var(--bd);
  border-radius:10px; padding:0.7rem 0.9rem; margin-bottom:0.5rem;
}}
.tl-change-what {{ font-size:0.84rem; font-weight:700; color:var(--tx); margin-bottom:0.15rem; }}
.tl-change-why  {{ font-size:0.77rem; color:var(--tx2); line-height:1.5; }}
.tl-change-modern {{ font-size:0.72rem; color:var(--p1); margin-top:0.2rem; }}
.tl-fact-box {{
  background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(139,92,246,0.06));
  border:1px solid rgba(99,102,241,0.18); border-radius:12px;
  padding:0.9rem 1.1rem; margin-bottom:0.75rem;
}}
.tl-fact-title {{ font-size:0.63rem; font-weight:700; letter-spacing:2px; color:var(--p1); text-transform:uppercase; margin-bottom:0.5rem; }}
.tl-fact-item {{ font-size:0.78rem; color:var(--tx2); padding:0.22rem 0; display:flex; align-items:flex-start; gap:0.5rem; }}
.tl-diff-bar {{
  display:flex; align-items:center; gap:1rem; margin:0.9rem 0;
  background:var(--sf2); border-radius:10px; padding:0.7rem 1rem;
  border:1px solid var(--bd);
}}
.tl-diff-label {{ font-size:0.7rem; color:var(--mt); font-weight:600; min-width:80px; }}
.tl-diff-track {{ flex:1; height:8px; background:var(--bd); border-radius:4px; overflow:hidden; }}
.tl-diff-fill  {{ height:100%; border-radius:4px; background:linear-gradient(90deg,var(--p1),var(--p2)); }}
.speculative-badge {{
  display:inline-block; background:rgba(245,158,11,0.12);
  border:1px solid rgba(245,158,11,0.35); color:#F59E0B;
  border-radius:6px; padding:0.18rem 0.6rem; font-size:0.68rem; font-weight:700;
  margin-left:0.5rem; letter-spacing:1px;
}}

/* ── CODE DNA ── */
.dna-archetype-card {{
  background:linear-gradient(135deg,var(--p1) 0%,var(--p2) 60%,#06B6D4 100%);
  border-radius:18px; padding:1.8rem; text-align:center;
  margin-bottom:1rem; box-shadow:0 8px 32px var(--glow);
  position:relative; overflow:hidden;
}}
.dna-archetype-card::before {{
  content:''; position:absolute; inset:0;
  background:radial-gradient(circle at 30% 50%,rgba(255,255,255,0.08),transparent 60%);
}}
.dna-archetype-icon {{ font-size:3rem; margin-bottom:0.5rem; display:block; }}
.dna-archetype-name {{
  font-size:1.4rem; font-weight:900; color:white;
  letter-spacing:-0.5px; margin-bottom:0.3rem;
}}
.dna-archetype-sub {{ font-size:0.8rem; color:rgba(255,255,255,0.8); line-height:1.6; }}
.dna-score-ring {{
  width:80px; height:80px; border-radius:50%;
  background:conic-gradient(var(--p1) calc(var(--pct)*1%), var(--sf2) 0);
  display:flex; align-items:center; justify-content:center;
  margin:0 auto 0.5rem; position:relative;
}}
.dna-score-ring::before {{
  content:''; position:absolute; inset:10px; border-radius:50%; background:var(--sf);
}}
.dna-score-val {{ position:relative; font-size:1.1rem; font-weight:800; color:var(--p1); z-index:1; }}
.dna-gene-row {{
  display:flex; align-items:center; gap:0.75rem;
  padding:0.6rem 0; border-bottom:1px solid var(--bd);
}}
.dna-gene-row:last-child {{ border-bottom:none; }}
.dna-gene-name {{ font-size:0.78rem; font-weight:600; color:var(--tx); min-width:130px; }}
.dna-gene-track {{ flex:1; height:7px; background:var(--bd); border-radius:4px; overflow:hidden; }}
.dna-gene-fill  {{ height:100%; border-radius:4px; }}
.dna-gene-label {{ font-size:0.67rem; color:var(--mt); min-width:100px; text-align:right; }}
.dna-power-card {{
  background:var(--sf); border:1px solid rgba(16,185,129,0.25);
  border-radius:12px; padding:0.8rem 1rem; margin-bottom:0.5rem;
}}
.dna-power-title {{ font-size:0.86rem; font-weight:700; color:#10B981; margin-bottom:0.18rem; display:flex; align-items:center; gap:0.4rem; }}
.dna-power-desc  {{ font-size:0.77rem; color:var(--tx2); line-height:1.5; }}
.dna-blind-card {{
  background:var(--sf); border:1px solid rgba(239,68,68,0.22);
  border-radius:12px; padding:0.8rem 1rem; margin-bottom:0.5rem;
}}
.dna-blind-title {{ font-size:0.86rem; font-weight:700; color:#EF4444; margin-bottom:0.18rem; display:flex; align-items:center; gap:0.4rem; }}
.dna-blind-desc  {{ font-size:0.77rem; color:var(--tx2); line-height:1.5; }}
.dna-compat-tag {{
  display:inline-block; background:rgba(99,102,241,0.12);
  border:1px solid rgba(99,102,241,0.25); color:var(--p1);
  border-radius:20px; padding:0.22rem 0.75rem; font-size:0.72rem;
  font-weight:600; margin:0.18rem;
}}
.dna-famous-box {{
  background:linear-gradient(135deg,rgba(245,158,11,0.07),rgba(239,68,68,0.07));
  border:1px solid rgba(245,158,11,0.22); border-radius:12px;
  padding:0.85rem 1.1rem; display:flex; align-items:center; gap:0.9rem;
}}
.dna-famous-icon {{ font-size:1.6rem; }}
.dna-famous-label {{ font-size:0.63rem; color:var(--mt); text-transform:uppercase; letter-spacing:1.5px; font-weight:700; }}
.dna-famous-name  {{ font-size:0.9rem; font-weight:800; color:#F59E0B; }}

/* ── INTERVIEW ── */
.iv-header {{
  background:linear-gradient(135deg,var(--sf),var(--sf2));
  border:1px solid var(--bd); border-radius:16px;
  padding:1.2rem 1.5rem; margin-bottom:1rem;
  display:flex; align-items:center; gap:1rem;
}}
.iv-header-icon {{ font-size:2.2rem; }}
.iv-company-badge {{
  display:inline-flex; align-items:center; gap:0.35rem;
  background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.25);
  border-radius:20px; padding:0.2rem 0.7rem; font-size:0.7rem;
  font-weight:700; color:var(--p1); margin-bottom:0.35rem;
}}
.iv-title  {{ font-size:1.1rem; font-weight:800; color:var(--tx); }}
.iv-sub    {{ font-size:0.77rem; color:var(--mt); }}
.iv-progress-row {{
  display:flex; align-items:center; gap:0.6rem; margin-bottom:1rem;
}}
.iv-step {{
  width:32px; height:32px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-size:0.72rem; font-weight:800; flex-shrink:0;
  border:2px solid var(--bd); color:var(--mt);
}}
.iv-step.done  {{ background:var(--p1); border-color:var(--p1); color:white; }}
.iv-step.active{{ background:rgba(99,102,241,0.18); border-color:var(--p1); color:var(--p1); }}
.iv-step-line  {{ flex:1; height:2px; background:var(--bd); }}
.iv-step-line.done {{ background:var(--p1); }}
.iv-question-card {{
  background:var(--sf); border:1px solid var(--bd);
  border-left:4px solid var(--p1);
  border-radius:14px; padding:1.2rem 1.4rem; margin-bottom:0.85rem;
  box-shadow:var(--shadow);
}}
.iv-q-meta  {{ display:flex; align-items:center; gap:0.6rem; margin-bottom:0.65rem; flex-wrap:wrap; }}
.iv-q-badge {{
  border-radius:6px; padding:0.1rem 0.48rem; font-size:0.63rem; font-weight:700;
  text-transform:uppercase; letter-spacing:0.8px;
}}
.iv-q-easy   {{ background:rgba(16,185,129,0.12);  color:#10B981; }}
.iv-q-medium {{ background:rgba(245,158,11,0.12);  color:#F59E0B; }}
.iv-q-hard   {{ background:rgba(239,68,68,0.12);   color:#EF4444; }}
.iv-q-focus  {{ background:rgba(99,102,241,0.10);  color:var(--p1); font-size:0.63rem; font-weight:600; border-radius:6px; padding:0.1rem 0.48rem; }}
.iv-q-text   {{ font-size:0.95rem; font-weight:600; color:var(--tx); line-height:1.6; }}
.iv-hint-box {{
  background:rgba(6,182,212,0.06); border:1px solid rgba(6,182,212,0.18);
  border-radius:8px; padding:0.5rem 0.8rem; margin-top:0.6rem;
  font-size:0.77rem; color:#06B6D4;
}}
.iv-eval-box {{
  background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.2);
  border-radius:10px; padding:0.75rem 1rem; margin-bottom:0.75rem;
  font-size:0.82rem; color:var(--tx2); line-height:1.55;
}}
.iv-eval-box strong {{ color:#10B981; }}
.iv-verdict-card {{
  border-radius:16px; padding:1.5rem; text-align:center; margin-bottom:1rem;
}}
.verdict-strong-hire {{ background:linear-gradient(135deg,rgba(16,185,129,0.12),rgba(6,182,212,0.12)); border:2px solid #10B981; }}
.verdict-hire        {{ background:linear-gradient(135deg,rgba(99,102,241,0.10),rgba(16,185,129,0.10)); border:2px solid var(--p1); }}
.verdict-no-hire     {{ background:linear-gradient(135deg,rgba(245,158,11,0.10),rgba(239,68,68,0.10)); border:2px solid #F59E0B; }}
.verdict-strong-no-hire {{ background:linear-gradient(135deg,rgba(239,68,68,0.12),rgba(239,68,68,0.06)); border:2px solid #EF4444; }}
.iv-verdict-emoji  {{ font-size:2.5rem; margin-bottom:0.5rem; }}
.iv-verdict-label  {{ font-size:1.3rem; font-weight:900; margin-bottom:0.5rem; }}
.iv-score-big      {{ font-size:3rem; font-weight:900; color:var(--p1); line-height:1; }}
.iv-score-sub      {{ font-size:0.7rem; color:var(--mt); text-transform:uppercase; letter-spacing:2px; }}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════════

def sev_badge(sev: str) -> str:
    s = (sev or "").lower()
    cls = {"critical":"sev-critical","high":"sev-high","medium":"sev-medium"}.get(s,"sev-low")
    return f'<span class="{cls}">{(sev or "info").upper()}</span>'


def render_review_section(items: list, css_cls: str, icon: str, title: str, kind: str) -> str:
    count = len(items)
    html = f'<div class="rv {css_cls}"><div class="rv-hdr">{icon} {title} <span style="opacity:0.55;font-size:0.73rem;font-weight:500;">({count})</span></div>'
    if not items:
        html += '<div style="color:#64748B;font-size:0.79rem;padding:0.28rem 0;">✓ No issues found</div>'
    for item in items:
        t = item.get("title","")
        d = item.get("description","")
        html += f'<div class="rv-item"><div class="rv-item-title">{t}'
        if "severity" in item:
            html += f' {sev_badge(item["severity"])}'
        html += f'</div><div class="rv-item-desc">{d}</div>'
        if kind == "bugs":
            if item.get("line_hint"):
                html += f'<div class="rv-item-meta">📍 {item["line_hint"]}</div>'
            if item.get("fix"):
                html += f'<div class="rv-item-fix">🔧 Fix: {item["fix"]}</div>'
        if kind == "performance":
            if item.get("suggestion"):
                html += f'<div class="rv-item-fix">💡 {item["suggestion"]}</div>'
            if item.get("impact"):
                html += f'<div class="rv-item-meta">📈 {item["impact"]}</div>'
        if kind == "security":
            if item.get("cve_type"):
                html += f'<div class="rv-item-meta">🏷️ {item["cve_type"]}</div>'
            if item.get("fix"):
                html += f'<div class="rv-item-fix">🔧 {item["fix"]}</div>'
        if kind == "best":
            if item.get("reference"):
                html += f'<div class="rv-item-meta">📚 {item["reference"]}</div>'
            if item.get("example"):
                html += f'<div class="rv-item-fix">💻 {item["example"]}</div>'
        html += '</div>'
    html += '</div>'
    return html


def ide_header(lang: str, label: str, color: str = "var(--mt)") -> None:
    """Render a fake IDE top-bar above a textarea."""
    st.markdown(f"""
    <div class="ide-wrap">
      <div class="ide-topbar">
        <span class="ide-dot-r"></span>
        <span class="ide-dot-y"></span>
        <span class="ide-dot-g"></span>
        <span style="font-size:0.72rem;font-weight:600;color:{color};margin-left:0.4rem;">{label}</span>
        <span class="ide-lang-tag">{lang}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _need_key() -> bool:
    if not st.session_state.api_key.strip():
        st.markdown('<div class="msg-warn">⚠️ Enter your Groq API key in the sidebar to use AI features.</div>', unsafe_allow_html=True)
        return True
    return False


# ════════════════════════════════════════════════════════════════════════════════
#  AUTH PAGES
# ════════════════════════════════════════════════════════════════════════════════

def page_login():
    _, col, _ = st.columns([1, 1.45, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1rem;">
          <span class="brand-logo">⚡ CodeRefine</span>
          <p class="brand-tag">Smarter Code. Cleaner Future.</p>
        </div>
        <div style="text-align:center;margin-bottom:1.5rem;">
          <span class="pill">🐞 Bug Detection</span><span class="pill">⚡ Performance</span>
          <span class="pill">🔐 Security</span><span class="pill">✨ AI Rewrite</span>
          <span class="pill">🌐 Translator</span><span class="pill">🎯 Challenges</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="auth-card"><div class="card-title">Welcome back</div><div class="card-sub">Sign in to your workspace</div></div>', unsafe_allow_html=True)

        if st.session_state.signup_success:
            st.markdown('<div class="msg-ok">✓ Account created! Sign in below.</div>', unsafe_allow_html=True)
            st.session_state.signup_success = False
        if st.session_state.login_error:
            st.markdown(f'<div class="msg-err">✗ {st.session_state.login_error}</div>', unsafe_allow_html=True)
            st.session_state.login_error = None

        username = st.text_input("Username", placeholder="Your username", key="li_user")
        password = st.text_input("Password", placeholder="Your password", type="password", key="li_pass")
        st.write("")
        if st.button("Sign In →", key="btn_login", use_container_width=True):
            if not username.strip() or not password:
                st.session_state.login_error = "Please fill in all fields."
                st.rerun()
            else:
                u = authenticate_user(username.strip(), password)
                if u:
                    st.session_state.user   = u
                    st.session_state.theme  = u.get("theme", "dark")
                    st.session_state.accent = u.get("accent_color", "indigo")
                    st.session_state.page   = "dashboard"
                    st.rerun()
                else:
                    st.session_state.login_error = "Invalid username or password."
                    st.rerun()
        st.markdown('<div class="divider">or</div>', unsafe_allow_html=True)
        if st.button("Create free account →", key="goto_signup", use_container_width=True):
            st.session_state.page = "signup"; st.rerun()


def page_signup():
    _, col, _ = st.columns([1, 1.45, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1rem;">
          <span class="brand-logo">⚡ CodeRefine</span>
          <p class="brand-tag">Smarter Code. Cleaner Future.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="auth-card"><div class="card-title">Create your account</div><div class="card-sub">Join developers shipping better code</div></div>', unsafe_allow_html=True)

        if st.session_state.signup_error:
            st.markdown(f'<div class="msg-err">✗ {st.session_state.signup_error}</div>', unsafe_allow_html=True)
            st.session_state.signup_error = None

        username = st.text_input("Username", placeholder="Choose a username (3+ chars)", key="su_user")
        email    = st.text_input("Email", placeholder="you@example.com", key="su_email")
        password = st.text_input("Password", placeholder="Min. 8 characters", type="password", key="su_pass")
        confirm  = st.text_input("Confirm Password", placeholder="Repeat password", type="password", key="su_conf")
        st.write("")
        if st.button("Create Account →", key="btn_signup", use_container_width=True):
            err = None
            if not all([username.strip(), email.strip(), password, confirm]):
                err = "Please fill in all fields."
            elif len(username.strip()) < 3:
                err = "Username must be ≥ 3 characters."
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email.strip()):
                err = "Please enter a valid email."
            elif len(password) < 8:
                err = "Password must be ≥ 8 characters."
            elif password != confirm:
                err = "Passwords do not match."
            if err:
                st.session_state.signup_error = err; st.rerun()
            else:
                ok, msg = create_user(username.strip(), email.strip(), password)
                if ok:
                    st.session_state.signup_success = True
                    st.session_state.page = "login"; st.rerun()
                else:
                    st.session_state.signup_error = msg; st.rerun()
        st.markdown('<div class="divider">or</div>', unsafe_allow_html=True)
        if st.button("← Back to Sign In", key="goto_login", use_container_width=True):
            st.session_state.page = "login"; st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    user = st.session_state.user

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div class="sb-brand">⚡ CodeRefine</div>
        <div class="sb-tag">Smarter Code. Cleaner Future.</div>
        <div class="user-chip">
          <div class="u-av">{user['username'][0].upper()}</div>
          <div style="min-width:0;flex:1;">
            <div class="u-name">{user['username']}</div>
            <div class="u-role">● Online</div>
          </div>
        </div>
        <div class="sb-div"></div>
        <div class="sb-sec">Navigation</div>
        """, unsafe_allow_html=True)

        nav = st.radio("nav", [
            "🔍  Code Review",
            "✍️  Rewrite Code",
            "🌐  Translate",
            "💡  Explain",
            "⏳  Timeline",
            "🧬  Code DNA",
            "🎤  Interview",
            "💾  Snippets",
            "🎯  Challenges",
            "📊  Analytics",
            "⚙️  Settings",
        ], label_visibility="collapsed", key="nav_radio")

        st.markdown('<div class="sb-div"></div><div class="sb-sec">Groq API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "key", value=st.session_state.api_key, type="password",
            placeholder="gsk_...", key="api_key_input", label_visibility="collapsed",
        )
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            from ai_engine import reset_client; reset_client()

        st.markdown('<div class="sb-div"></div><div class="sb-sec">Recent Reviews</div>', unsafe_allow_html=True)
        for h in get_user_history(user["id"], limit=4):
            ts  = h["created_at"][:10] if h.get("created_at") else "—"
            snp = (h["original_code"][:28]+"…") if len(h.get("original_code",""))>28 else h.get("original_code","")
            st.markdown(f'<div class="hist-item"><span class="lang-badge">{h["language"]}</span><div class="hist-snip">{snp}</div><div class="hist-meta">🐞{h["bugs_count"]} · ⚡{h["perf_score"]}% · {ts}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
        if st.button("⎋  Sign Out", key="btn_logout"):
            for k in list(_DEFAULTS.keys()):
                st.session_state[k] = _DEFAULTS[k]
            st.rerun()

    # ── Stats bar ─────────────────────────────────────────────────────────────
    stats = get_user_stats(user["id"])
    tot_rev  = int(stats.get("total_reviews") or 0)
    tot_bugs = int(stats.get("total_bugs")    or 0)
    tot_sec  = int(stats.get("total_security")or 0)
    avg_perf = round(float(stats.get("avg_perf")         or 0), 1)
    avg_conf = round(float(stats.get("avg_confidence")   or 0), 1)
    avg_cx   = round(float(stats.get("avg_complexity")   or 0), 1)

    sc = st.columns(6)
    mdata = [
        ("📂",str(tot_rev),   "Reviews",   "#6366F1,#8B5CF6"),
        ("🐞",str(tot_bugs),  "Bugs Found","#EF4444,#F87171"),
        ("🔐",str(tot_sec),   "Security",  "#10B981,#34D399"),
        ("⚡",f"{avg_perf}%", "Avg Perf",  "#F59E0B,#FBBF24"),
        ("🎯",f"{avg_conf}%", "Confidence","#06B6D4,#22D3EE"),
        ("🧩",str(avg_cx),    "Complexity","#8B5CF6,#A78BFA"),
    ]
    for col, (ico, val, lbl, grad) in zip(sc, mdata):
        with col:
            st.markdown(
                f'<div class="stat-card" style="--c-grad:linear-gradient(90deg,{grad});">'
                f'<div class="stat-icon">{ico}</div>'
                f'<div class="stat-val">{val}</div>'
                f'<div class="stat-label">{lbl}</div>'
                f'</div>', unsafe_allow_html=True
            )

    st.divider()

    nav_key = nav.split("  ")[-1]

    # ════════════════════════════════════════════════════════════════════════
    #  CODE REVIEW
    # ════════════════════════════════════════════════════════════════════════
    if nav_key == "Code Review":
        st.markdown('<div class="pg-title">Code Review</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Deep AI analysis — real bugs with fixes, performance, security, and best practices.</div>', unsafe_allow_html=True)

        col_in, col_meta = st.columns([1.15, 0.85], gap="large")
        with col_in:
            language = st.selectbox("Language", LANGUAGES, key="rv_lang")
            ide_header(language, "Source Code")
            code_input = st.text_area(
                "code", height=360, key="code_input_rv", label_visibility="collapsed",
                placeholder=f"# Paste your {language} code here…\n# Model: llama-3.3-70b-versatile (Groq)",
            )
            n = len(code_input)
            cls = "danger" if n > 8000 else "warn" if n > 5000 else ""
            st.markdown(f'<div class="char-cnt {cls}">{n:,} chars · ~{max(1,n//4):,} tokens · llama-3.3-70b-versatile</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                review_btn = st.button("🔍 Analyze Code", key="btn_rv", use_container_width=True, type="primary")
            with c2:
                if st.button("💾 Save as Snippet", key="btn_save_snip_rv", use_container_width=True):
                    if code_input.strip():
                        save_snippet(user["id"], f"Snippet {datetime.now().strftime('%m/%d %H:%M')}", "", language, code_input, [])
                        st.success("Saved!")

        with col_meta:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-hdr">📊 ANALYSIS SCORES</div>', unsafe_allow_html=True)
            if st.session_state.cx_score is not None:
                cx = st.session_state.cx_score
                cf = st.session_state.cf_score or 0
                ps = (st.session_state.review_result or {}).get("perf_score", 0)
                verdict = (st.session_state.review_result or {}).get("quality_verdict", "needs_work")
                cx_c  = "#EF4444" if cx > 70 else "#F59E0B" if cx > 40 else "#10B981"
                cx_gr = "#EF4444,#F87171" if cx > 70 else "#F59E0B,#FBBF24" if cx > 40 else "#10B981,#34D399"
                st.markdown(f"""
                <div class="score-grid">
                  <div class="score-item"><div class="score-val" style="color:{cx_c};">{cx}</div><div class="score-lbl">Complexity</div></div>
                  <div class="score-item"><div class="score-val" style="color:{'#10B981' if cf>=80 else '#F59E0B' if cf>=60 else '#EF4444'};">{cf}</div><div class="score-lbl">Confidence</div></div>
                  <div class="score-item"><div class="score-val" style="color:{'#10B981' if ps>=70 else '#F59E0B' if ps>=40 else '#EF4444'};">{ps}</div><div class="score-lbl">Perf</div></div>
                </div>
                <div style="font-size:0.67rem;color:var(--mt);margin-bottom:0.22rem;">Code Complexity</div>
                <div class="cx-bar"><div class="cx-fill" style="width:{cx}%;background:linear-gradient(90deg,{cx_gr});"></div></div>
                <div style="margin-top:0.55rem;"><span class="verdict-{verdict}">Verdict: {verdict.replace('_',' ').title()}</span></div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:var(--mt);font-size:0.78rem;min-height:70px;display:flex;align-items:center;">Run analysis to see scores.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if review_btn:
            if not _need_key():
                if len(code_input.strip()) < 10:
                    st.error("Please paste at least 10 characters of code.")
                else:
                    from ai_engine import review_code as ai_rv
                    with st.spinner("🧠 Analyzing with llama-3.3-70b-versatile…"):
                        try:
                            result = ai_rv(st.session_state.api_key, code_input, language)
                            st.session_state.review_result   = result
                            st.session_state.review_language = language
                            st.session_state.review_code     = code_input
                            st.session_state.cx_score        = result.get("complexity", 50)
                            st.session_state.cf_score        = result.get("confidence", 80)
                            save_review(user["id"], language, code_input, json.dumps(result), "",
                                len(result.get("bugs",[])), result.get("perf_score",0),
                                len(result.get("security",[])), result.get("complexity",0), result.get("confidence",0))
                        except Exception as e:
                            st.error(f"Error: {e}")
                    st.rerun()

        if st.session_state.review_result:
            r = st.session_state.review_result
            if r.get("_raw"):
                st.markdown(f'<div class="msg-warn">⚠️ JSON parse issue. Raw response preview: {r["_raw"][:200]}</div>', unsafe_allow_html=True)
            if r.get("summary"):
                st.markdown(f'<div class="summary-box"><div class="summary-label">🧠 AI Summary</div><div class="summary-text">{r["summary"]}</div></div>', unsafe_allow_html=True)

            with st.expander(f"🐞 Bugs & Errors — {len(r.get('bugs',[]))} found", expanded=True):
                st.markdown(render_review_section(r.get("bugs",[]), "rv-bugs", "🐞", "Bugs & Errors", "bugs"), unsafe_allow_html=True)
            with st.expander(f"⚡ Performance — {len(r.get('performance',[]))} issues"):
                st.markdown(render_review_section(r.get("performance",[]), "rv-perf", "⚡", "Performance", "performance"), unsafe_allow_html=True)
            with st.expander(f"🔐 Security — {len(r.get('security',[]))} vulnerabilities"):
                st.markdown(render_review_section(r.get("security",[]), "rv-sec", "🔐", "Security", "security"), unsafe_allow_html=True)
            with st.expander(f"📘 Best Practices — {len(r.get('best_practices',[]))} items"):
                st.markdown(render_review_section(r.get("best_practices",[]), "rv-best", "📘", "Best Practices", "best"), unsafe_allow_html=True)

            ts = datetime.now().strftime('%Y%m%d_%H%M')
            txt = (
                f"CodeRefine Review — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"Language: {st.session_state.review_language}\n"
                f"Complexity: {r.get('complexity')} | Confidence: {r.get('confidence')}% | Perf: {r.get('perf_score')}%\n\n"
                f"SUMMARY\n{'='*60}\n{r.get('summary','')}\n\n"
                "BUGS\n" + "="*60 + "\n" +
                "\n".join(f"• [{i.get('severity','').upper()}] {i.get('title','')} — {i.get('description','')}\n  Fix: {i.get('fix','')}" for i in r.get("bugs",[])) +
                "\n\nPERFORMANCE\n" + "="*60 + "\n" +
                "\n".join(f"• {i.get('title','')} — {i.get('suggestion','')}" for i in r.get("performance",[])) +
                "\n\nSECURITY\n" + "="*60 + "\n" +
                "\n".join(f"• [{i.get('cve_type','')}] {i.get('title','')} — {i.get('description','')}" for i in r.get("security",[])) +
                "\n\nBEST PRACTICES\n" + "="*60 + "\n" +
                "\n".join(f"• {i.get('title','')} — {i.get('description','')}" for i in r.get("best_practices",[]))
            )
            d1, d2, d3 = st.columns(3)
            with d1: st.download_button("📥 Download .txt", txt, f"review_{ts}.txt", "text/plain", use_container_width=True)
            with d2: st.download_button("📋 Export JSON", json.dumps(r, indent=2), f"review_{ts}.json", "application/json", use_container_width=True)
            with d3:
                if st.button("🗑️ Clear", key="clear_rv", use_container_width=True):
                    st.session_state.review_result = st.session_state.cx_score = st.session_state.cf_score = None
                    st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  REWRITE CODE
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Rewrite Code":
        st.markdown('<div class="pg-title">Rewrite Code</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">AI produces a production-grade rewrite, then auto-reviews the result to verify quality.</div>', unsafe_allow_html=True)

        default_code = st.session_state.review_code or ""
        default_lang = st.session_state.review_language or "Python"
        lang_idx = LANGUAGES.index(default_lang) if default_lang in LANGUAGES else 0
        rw_lang  = st.selectbox("Language", LANGUAGES, index=lang_idx, key="rw_lang_sel")

        col_o, col_r = st.columns(2, gap="large")
        with col_o:
            ide_header(rw_lang, "Original Code", "#EF4444")
            original = st.text_area("orig", value=default_code, height=400,
                placeholder=f"# Paste your {rw_lang} code to rewrite…",
                key="rw_orig", label_visibility="collapsed")
            st.markdown(f'<div class="char-cnt">{len(original):,} chars</div>', unsafe_allow_html=True)
        with col_r:
            rw_result = st.session_state.rw_result
            rw_code   = (rw_result or {}).get("rewritten_code", "")
            ide_header(rw_lang, "Rewritten Code ✨", "#10B981")
            st.text_area("rw_out", value=rw_code or "# Rewritten code will appear here…",
                height=400, key="rw_display", label_visibility="collapsed")

        st.write("")
        b1, b2, b3 = st.columns([2, 1, 1])
        with b1:
            rw_btn = st.button("✨ Rewrite with AI", key="btn_rw", type="primary", use_container_width=True)
        with b2:
            if rw_result and rw_code and len(rw_code) > 20:
                ext = {"Python":"py","JavaScript":"js","TypeScript":"ts","Java":"java","C++":"cpp","C":"c","C#":"cs","Go":"go","Rust":"rs"}.get(rw_lang,"txt")
                st.download_button("📥 Download", rw_code, f"refactored.{ext}", "text/plain", use_container_width=True)
        with b3:
            if st.button("🗑️ Clear", key="clear_rw", use_container_width=True):
                st.session_state.rw_result = None; st.rerun()

        if rw_btn:
            if not _need_key():
                if len(original.strip()) < 10:
                    st.error("Please paste some code to rewrite.")
                else:
                    from ai_engine import rewrite_code as ai_rw, review_code as ai_rv
                    with st.spinner("✨ Rewriting with llama-3.3-70b-versatile…"):
                        try:
                            result = ai_rw(st.session_state.api_key, original, rw_lang)
                            st.session_state.rw_result   = result
                            st.session_state.rw_language = rw_lang
                            ot  = result.get("orig_time_complexity","O(n)")
                            rt  = result.get("rw_time_complexity","O(n)")
                            os_ = result.get("orig_space_complexity","")
                            rs_ = result.get("rw_space_complexity","")
                            save_review(user["id"], rw_lang, original, "{}", result.get("rewritten_code","")[:3000],
                                0, 0, 0, 0, 0, ot, rt, complexity_to_score(ot), complexity_to_score(rt),
                                os_, rs_)
                        except Exception as e:
                            st.error(f"Error: {e}")
                    # Auto-review rewritten code
                    if st.session_state.rw_result and st.session_state.rw_result.get("rewritten_code"):
                        with st.spinner("🔍 Auto-reviewing rewritten code…"):
                            try:
                                ar = ai_rv(st.session_state.api_key,
                                    st.session_state.rw_result["rewritten_code"], rw_lang,
                                    context="This is an AI-rewritten version. Verify it is correct, bug-free, and improved.")
                                st.session_state.rw_result["auto_review"] = ar
                            except Exception:
                                pass
                    st.rerun()

        if rw_result and (rw_result.get("orig_time_complexity") or rw_result.get("rw_time_complexity")):
            ot = rw_result.get("orig_time_complexity","—")
            rt = rw_result.get("rw_time_complexity","—")
            os_ = rw_result.get("orig_space_complexity","—")
            rs_ = rw_result.get("rw_space_complexity","—")
            st.markdown(f"""
            <div style="background:var(--sf2);border:1px solid var(--bd);border-radius:13px;padding:1.1rem 1.4rem;margin:0.9rem 0;display:flex;align-items:center;gap:2rem;flex-wrap:wrap;">
              <div>
                <div style="font-size:0.59rem;color:var(--mt);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.22rem;">⏱ Original</div>
                <div style="font-size:1.5rem;font-weight:800;color:#EF4444;font-family:'JetBrains Mono',monospace;">{ot}</div>
                <div style="font-size:0.67rem;color:var(--mt);">Space: {os_}</div>
              </div>
              <div style="font-size:1.6rem;color:var(--p1);">→</div>
              <div>
                <div style="font-size:0.59rem;color:var(--mt);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.22rem;">✨ Rewritten</div>
                <div style="font-size:1.5rem;font-weight:800;color:#10B981;font-family:'JetBrains Mono',monospace;">{rt}</div>
                <div style="font-size:0.67rem;color:var(--mt);">Space: {rs_}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        if rw_result and rw_result.get("improvements"):
            st.markdown('<div class="pg-title" style="font-size:1.1rem;margin:0.8rem 0 0.55rem;">🔑 Improvements Made</div>', unsafe_allow_html=True)
            imps = rw_result["improvements"]
            cols = st.columns(min(len(imps), 2))
            for i, imp in enumerate(imps):
                with cols[i % 2]:
                    cat = imp.get("category","General").replace(" ","_")
                    st.markdown(f"""<div class="imp-card">
                      <div class="imp-cat {cat}">{imp.get('category','General')}</div>
                      <div class="imp-title">{imp.get('title','')}</div>
                      <div class="imp-desc">{imp.get('description','')}</div>
                      <div class="imp-impact">💡 {imp.get('impact','')}</div>
                    </div>""", unsafe_allow_html=True)

        if rw_result and rw_result.get("auto_review"):
            ar = rw_result["auto_review"]
            v  = ar.get("quality_verdict","good")
            st.markdown('<div class="pg-title" style="font-size:1.1rem;margin:1.1rem 0 0.55rem;">🔍 Auto-Review of Rewritten Code</div>', unsafe_allow_html=True)
            st.markdown(f"""<div class="summary-box">
              <div class="summary-label">Quality Verdict</div>
              <div style="display:flex;align-items:center;gap:0.9rem;flex-wrap:wrap;margin-bottom:0.45rem;">
                <span class="verdict-{v}">{v.replace('_',' ').title()}</span>
                <span style="font-size:0.79rem;color:var(--mt);">Perf {ar.get('perf_score',0)}% · Complexity {ar.get('complexity',0)} · Confidence {ar.get('confidence',0)}%</span>
              </div>
              <div class="summary-text">{ar.get('summary','')}</div>
            </div>""", unsafe_allow_html=True)
            ar_bugs = ar.get("bugs",[])
            if ar_bugs:
                with st.expander(f"⚠️ Remaining Issues — {len(ar_bugs)} found"):
                    st.markdown(render_review_section(ar_bugs,"rv-bugs","🐞","Remaining Issues","bugs"), unsafe_allow_html=True)
            else:
                st.markdown('<div class="msg-ok">✓ Rewritten code is clean — no bugs detected in auto-review!</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  TRANSLATE
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Translate":
        st.markdown('<div class="pg-title">Code Translator</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Translate code between 19 languages with idiomatic, production-quality output.</div>', unsafe_allow_html=True)

        t1, t2, t3 = st.columns([1, 0.2, 1])
        with t1: src_lang = st.selectbox("From", LANGUAGES, index=0, key="tr_src")
        with t2: st.markdown('<div style="display:flex;align-items:flex-end;height:100%;padding-bottom:0.4rem;justify-content:center;font-size:1.4rem;color:var(--p1);">⇄</div>', unsafe_allow_html=True)
        with t3: tgt_lang = st.selectbox("To", LANGUAGES, index=1, key="tr_tgt")

        col_s, col_o = st.columns(2, gap="large")
        with col_s:
            ide_header(src_lang, "Source Code")
            tr_code = st.text_area("tr_in", height=380,
                placeholder=f"# Paste your {src_lang} code…",
                key="tr_input", label_visibility="collapsed",
                value=st.session_state.review_code or "")
            st.markdown(f'<div class="char-cnt">{len(tr_code):,} chars</div>', unsafe_allow_html=True)
        with col_o:
            tr_result = st.session_state.translate_result
            out_code  = (tr_result or {}).get("translated_code","")
            ide_header(tgt_lang, "Translated Output", "var(--p1)")
            st.text_area("tr_out", value=out_code or "# Translation will appear here…", height=380, key="tr_display", label_visibility="collapsed")

        b1, b2, b3 = st.columns([2,1,1])
        with b1: tr_btn = st.button(f"🌐 Translate → {tgt_lang}", key="btn_tr", type="primary", use_container_width=True)
        with b2:
            if tr_result and out_code:
                ext = {"Python":"py","JavaScript":"js","TypeScript":"ts","Java":"java","Go":"go","Rust":"rs"}.get(tgt_lang,"txt")
                st.download_button("📥 Download", out_code, f"translated.{ext}", "text/plain", use_container_width=True)
        with b3:
            if st.button("🗑️ Clear", key="clear_tr", use_container_width=True):
                st.session_state.translate_result = None; st.rerun()

        if tr_btn:
            if not _need_key():
                if len(tr_code.strip()) < 10: st.error("Please paste code to translate.")
                elif src_lang == tgt_lang: st.error("Source and target must differ.")
                else:
                    from ai_engine import translate_code
                    with st.spinner(f"🌐 Translating {src_lang} → {tgt_lang}…"):
                        try:
                            st.session_state.translate_result = translate_code(st.session_state.api_key, tr_code, src_lang, tgt_lang)
                        except Exception as e:
                            st.error(f"Error: {e}")
                    st.rerun()

        if tr_result:
            if tr_result.get("notes"):
                st.markdown(f'<div class="summary-box"><div class="summary-label">📝 Translation Notes</div><div class="summary-text">{tr_result["notes"]}</div></div>', unsafe_allow_html=True)
            if tr_result.get("warnings"):
                st.markdown(f'<div class="msg-warn">⚠️ {tr_result["warnings"]}</div>', unsafe_allow_html=True)
            if tr_result.get("idiom_changes"):
                with st.expander(f"🔄 Idiomatic Adaptations — {len(tr_result['idiom_changes'])}"):
                    for ch in tr_result["idiom_changes"]:
                        st.markdown(f'<div class="imp-card"><div style="display:flex;gap:0.8rem;align-items:center;flex-wrap:wrap;"><code style="color:#EF4444;font-size:0.77rem;">{ch.get("original","")}</code><span style="color:var(--p1);">→</span><code style="color:#10B981;font-size:0.77rem;">{ch.get("translated","")}</code></div><div class="imp-desc" style="margin-top:0.35rem;">{ch.get("reason","")}</div></div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  EXPLAIN
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Explain":
        st.markdown('<div class="pg-title">Explain Code</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Get a clear, structured plain-English explanation of what any code does.</div>', unsafe_allow_html=True)
        exp_lang = st.selectbox("Language", LANGUAGES, key="exp_lang")
        ide_header(exp_lang, "Code to Explain")
        exp_code = st.text_area("exp_in", height=300, key="exp_input", label_visibility="collapsed",
            placeholder="# Paste any code to get a plain-English explanation…",
            value=st.session_state.review_code or "")
        if st.button("💡 Explain This Code", key="btn_exp", type="primary"):
            if not _need_key():
                if len(exp_code.strip()) < 10: st.error("Please paste some code.")
                else:
                    from ai_engine import explain_code
                    with st.spinner("💡 Generating explanation…"):
                        try:
                            st.session_state.explain_result = explain_code(st.session_state.api_key, exp_code, exp_lang)
                        except Exception as e:
                            st.error(f"Error: {e}")
                    st.rerun()
        if st.session_state.explain_result:
            st.markdown(f'<div class="summary-box"><div class="summary-label">💡 Explanation</div><div style="font-size:0.86rem;color:var(--tx2);line-height:1.75;white-space:pre-wrap;">{st.session_state.explain_result}</div></div>', unsafe_allow_html=True)
            if st.button("🗑️ Clear", key="clr_exp"):
                st.session_state.explain_result = None; st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  SNIPPETS
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Snippets":
        st.markdown('<div class="pg-title">Code Snippets</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Save, search, tag, and reuse your favorite code snippets.</div>', unsafe_allow_html=True)
        tab_browse, tab_new = st.tabs(["📚 Browse", "➕ New Snippet"])

        with tab_browse:
            sc1, sc2 = st.columns([2, 1])
            with sc1: sq = st.text_input("Search", placeholder="Title, description, or code…", key="snip_q", label_visibility="collapsed")
            with sc2: fl = st.selectbox("Language", ["All"]+LANGUAGES, key="snip_fl", label_visibility="collapsed")
            snippets = get_snippets(user["id"], search=sq or "", language="" if fl=="All" else fl)
            if not snippets:
                st.markdown('<div class="msg-warn">📭 No snippets yet. Create one in the New Snippet tab!</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:0.71rem;color:var(--mt);margin-bottom:0.7rem;">{len(snippets)} snippet{"s" if len(snippets)!=1 else ""}</div>', unsafe_allow_html=True)
                for s in snippets:
                    tags_html = " ".join(f'<span class="tag-badge">{t}</span>' for t in (s.get("tags") or []))
                    fav = "⭐" if s["is_favorite"] else "☆"
                    st.markdown(f"""<div class="snippet-card">
                      <div class="snippet-title">{fav} {s['title']} <span class="lang-badge">{s['language']}</span></div>
                      <div class="snippet-desc">{s.get('description','') or '—'}</div>
                      <div class="snippet-preview">{s['code'][:90].replace('<','&lt;').replace('>','&gt;')}</div>
                      <div class="snippet-meta">{tags_html}<span>📅 {s['created_at'][:10]}</span></div>
                    </div>""", unsafe_allow_html=True)
                    sa, sb, sc_, sd = st.columns(4)
                    with sa:
                        if st.button("📝 Use in Review", key=f"sr_{s['id']}"):
                            st.session_state.review_code = s["code"]
                            st.session_state.review_language = s["language"]; st.rerun()
                    with sb:
                        if st.button(f"{'★ Unfav' if s['is_favorite'] else '☆ Fav'}", key=f"sf_{s['id']}"):
                            toggle_snippet_favorite(s["id"], user["id"]); st.rerun()
                    with sc_:
                        if st.button("🗑️ Delete", key=f"sd_{s['id']}"):
                            delete_snippet(s["id"], user["id"]); st.rerun()
                    with sd:
                        pass
                    st.markdown("<hr style='border-color:var(--bd);margin:0.3rem 0;'>", unsafe_allow_html=True)

        with tab_new:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            ns_title = st.text_input("Title *", placeholder="e.g. Binary Search", key="ns_title")
            ns_desc  = st.text_input("Description", placeholder="What does it do?", key="ns_desc")
            ns_lang  = st.selectbox("Language", LANGUAGES, key="ns_lang")
            ide_header(ns_lang, "Snippet Code")
            ns_code  = st.text_area("ns_code_in", height=280, key="ns_code",
                label_visibility="collapsed",
                placeholder="# Your code here…",
                value=st.session_state.review_code or "")
            ns_tags  = st.text_input("Tags (comma-separated)", placeholder="algorithm, search…", key="ns_tags")
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("💾 Save Snippet", key="btn_save_snip", type="primary"):
                if not ns_title.strip(): st.error("Title required.")
                elif not ns_code.strip(): st.error("Code required.")
                else:
                    tags = [t.strip() for t in ns_tags.split(",") if t.strip()]
                    save_snippet(user["id"], ns_title.strip(), ns_desc.strip(), ns_lang, ns_code.strip(), tags)
                    st.success(f"✓ Snippet '{ns_title}' saved!"); st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  CHALLENGES
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Challenges":
        st.markdown('<div class="pg-title">Coding Challenges</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">AI-generated challenges tailored to your language and difficulty. Solve, get evaluated, improve.</div>', unsafe_allow_html=True)

        cs = get_challenge_stats(user["id"])
        cc = st.columns(4)
        cdata = [
            ("🎯",str(int(cs.get("total_attempts") or 0)),"Attempts","#6366F1,#8B5CF6"),
            ("✅",str(int(cs.get("total_passed")   or 0)),"Passed","#10B981,#34D399"),
            ("🏆",str(int(cs.get("best_score")     or 0)),"Best Score","#F59E0B,#FBBF24"),
            ("📊",f"{round(float(cs.get('avg_score') or 0),1)}","Avg Score","#06B6D4,#22D3EE"),
        ]
        for col, (ico, val, lbl, grad) in zip(cc, cdata):
            with col:
                st.markdown(f'<div class="stat-card" style="--c-grad:linear-gradient(90deg,{grad});text-align:center;"><div class="stat-icon">{ico}</div><div class="stat-val">{val}</div><div class="stat-label">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        gen_col, _ = st.columns([1.1, 0.9])
        with gen_col:
            st.markdown('<div class="panel"><div class="panel-hdr">🎲 GENERATE CHALLENGE</div>', unsafe_allow_html=True)
            g1, g2, g3 = st.columns(3)
            with g1: ch_lang = st.selectbox("Language", LANGUAGES, key="ch_lang")
            with g2: ch_diff = st.selectbox("Difficulty", ["easy","medium","hard"], key="ch_diff")
            with g3: ch_topic = st.selectbox("Topic", ["arrays","strings","recursion","dynamic programming","sorting","searching","graphs","trees","hash maps","linked lists","math","bit manipulation","greedy","backtracking"], key="ch_topic")
            gen_btn = st.button("🎲 Generate Challenge", key="btn_gen_ch", type="primary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if gen_btn:
            if not _need_key():
                from ai_engine import generate_challenge
                with st.spinner("🎲 Generating challenge…"):
                    try:
                        st.session_state.current_challenge = generate_challenge(st.session_state.api_key, ch_lang, ch_diff, ch_topic)
                        st.session_state.challenge_eval    = None
                        st.session_state.show_solution     = False
                    except Exception as e:
                        st.error(f"Error: {e}")
                st.rerun()

        if st.session_state.current_challenge:
            ch = st.session_state.current_challenge
            diff_cls = {"easy":"diff-easy","medium":"diff-medium","hard":"diff-hard"}.get(ch_diff if "ch_diff" in dir() else "medium","diff-medium")
            st.markdown(f"""<div class="challenge-card">
              <div style="display:flex;align-items:center;gap:0.65rem;margin-bottom:0.5rem;flex-wrap:wrap;">
                <div style="font-size:1.05rem;font-weight:800;color:var(--tx);">{ch.get('title','')}</div>
                <span class="diff-badge {diff_cls}">{ch_diff if "ch_diff" in dir() else "medium"}</span>
                <span style="font-size:0.68rem;color:var(--mt);">⏱ {ch.get('time_complexity','')}</span>
              </div>
              <div style="font-size:0.84rem;color:var(--tx2);line-height:1.7;white-space:pre-wrap;">{ch.get('description','')}</div>
              {"<div style='font-size:0.77rem;color:var(--mt);margin-top:0.5rem;'><strong>Constraints:</strong> " + " · ".join(ch.get('constraints',[])) + "</div>" if ch.get('constraints') else ""}
            </div>""", unsafe_allow_html=True)

            if ch.get("hints"):
                with st.expander("💡 Hints"):
                    for i, h in enumerate(ch["hints"],1):
                        st.markdown(f'<div style="color:var(--tx2);font-size:0.83rem;padding:0.25rem 0;">💡 {i}. {h}</div>', unsafe_allow_html=True)

            ide_header(ch_lang if "ch_lang" in dir() else "Python", "Your Solution")
            user_sol = st.text_area("ch_sol", value=ch.get("starter_code",""), height=260, key="ch_solution", label_visibility="collapsed")

            ev1, ev2, ev3 = st.columns(3)
            with ev1: eval_btn = st.button("🚀 Submit Solution", key="btn_eval", type="primary", use_container_width=True)
            with ev2:
                if st.button("👁 Show Solution", key="btn_show_sol", use_container_width=True):
                    st.session_state.show_solution = not st.session_state.get("show_solution",False)
            with ev3:
                if st.button("🔄 New Challenge", key="btn_new_ch", use_container_width=True):
                    st.session_state.current_challenge = st.session_state.challenge_eval = None; st.rerun()

            if st.session_state.get("show_solution") and ch.get("solution"):
                with st.expander("💡 Model Solution"):
                    st.code(ch["solution"], language=ch_lang.lower() if "ch_lang" in dir() and ch_lang in ["Python","JavaScript","Java","Go","Rust"] else "text")

            if eval_btn:
                if not _need_key():
                    from ai_engine import evaluate_challenge
                    with st.spinner("🤖 Evaluating…"):
                        try:
                            ev = evaluate_challenge(st.session_state.api_key, user_sol, ch, ch_lang if "ch_lang" in dir() else "Python")
                            st.session_state.challenge_eval = ev
                            save_challenge_attempt(user["id"], ch.get("title",""), ch_lang if "ch_lang" in dir() else "Python",
                                user_sol, ev.get("score",0), ev.get("passed",False), ev.get("feedback",""))
                        except Exception as e:
                            st.error(f"Error: {e}")
                    st.rerun()

            if st.session_state.challenge_eval:
                ev = st.session_state.challenge_eval
                sc_ = ev.get("score",0)
                passed = ev.get("passed",False)
                sc_col = "#10B981" if sc_ >= 80 else "#F59E0B" if sc_ >= 50 else "#EF4444"
                st.markdown(f"""
                <div style="background:var(--sf2);border:1px solid {'rgba(16,185,129,0.3)' if passed else 'rgba(239,68,68,0.3)'};border-radius:13px;padding:1.1rem 1.3rem;margin:0.9rem 0;">
                  <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:0.65rem;">
                    <div style="font-size:1.9rem;font-weight:900;color:{sc_col};">{sc_}/100</div>
                    <div>
                      <div style="font-size:0.87rem;font-weight:700;color:{'#10B981' if passed else '#EF4444'};">{'✅ Passed!' if passed else '❌ Not Passing'}</div>
                      <div style="font-size:0.73rem;color:var(--mt);">{ev.get('correctness','').title()} · {ev.get('time_complexity','')}</div>
                    </div>
                  </div>
                  <div style="font-size:0.83rem;color:var(--tx2);line-height:1.65;">{ev.get('feedback','')}</div>
                </div>
                """, unsafe_allow_html=True)
                if ev.get("improvements"):
                    st.markdown('<div style="font-size:0.72rem;font-weight:700;color:var(--mt);text-transform:uppercase;letter-spacing:1px;margin:0.5rem 0 0.35rem;">Suggestions</div>', unsafe_allow_html=True)
                    for imp in ev["improvements"]:
                        st.markdown(f'<div style="font-size:0.8rem;color:var(--tx2);padding:0.22rem 0;border-bottom:1px solid var(--bd);">• {imp}</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  ANALYTICS
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Analytics":
        st.markdown('<div class="pg-title">Analytics</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Your personal code quality metrics and review history.</div>', unsafe_allow_html=True)
        if tot_rev == 0:
            st.markdown('<div class="msg-warn">📊 No reviews yet. Run your first code review to see analytics!</div>', unsafe_allow_html=True)
        else:
            lang_data  = get_language_breakdown(user["id"])
            trend_data = get_recent_trend(user["id"], limit=10)
            cl, ct = st.columns(2, gap="large")
            with cl:
                st.markdown('<div class="panel"><div class="panel-hdr">📊 LANGUAGE BREAKDOWN</div>', unsafe_allow_html=True)
                total = sum(d["cnt"] for d in lang_data)
                for d in lang_data:
                    pct = int(d["cnt"]/total*100) if total else 0
                    st.markdown(f"""<div style="margin-bottom:0.6rem;">
                      <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
                        <span style="font-size:0.81rem;color:var(--tx);font-weight:600;">{d['language']}</span>
                        <span style="font-size:0.75rem;color:var(--mt);">{d['cnt']} · {pct}%</span>
                      </div>
                      <div class="cx-bar"><div class="cx-fill" style="width:{pct}%;background:linear-gradient(90deg,var(--p1),var(--p2));"></div></div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with ct:
                st.markdown('<div class="panel"><div class="panel-hdr">📈 PERFORMANCE TREND</div>', unsafe_allow_html=True)
                if trend_data:
                    import pandas as pd
                    df = pd.DataFrame(trend_data)
                    df["#"] = [f"#{i+1}" for i in range(len(df))]
                    df = df.set_index("#")
                    st.line_chart(df[["perf_score"]], color=["#10B981"], height=150, use_container_width=True)
                    if df["orig_complexity_score"].sum() + df["rw_complexity_score"].sum() > 0:
                        st.markdown('<div style="font-size:0.69rem;color:var(--p1);font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0.7rem 0 0.25rem;">Algorithm Efficiency (higher=faster)</div>', unsafe_allow_html=True)
                        tc = df[["orig_complexity_score","rw_complexity_score"]].copy()
                        tc.columns = ["Original","Rewritten"]
                        st.line_chart(tc, color=["#EF4444","#10B981"], height=130, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel"><div class="panel-hdr">📋 REVIEW HISTORY</div>', unsafe_allow_html=True)
            all_h = get_user_history(user["id"], limit=50)
            if all_h:
                import pandas as pd
                df2 = pd.DataFrame(all_h).rename(columns={
                    "language":"Language","bugs_count":"Bugs","perf_score":"Perf %",
                    "security_count":"Security","complexity":"Complexity","confidence":"Confidence %",
                    "orig_time_complexity":"Time O(·) Before","rw_time_complexity":"Time O(·) After",
                    "orig_space_complexity":"Space O(·) Before","rw_space_complexity":"Space O(·) After",
                    "created_at":"Date",
                })
                df2["Date"] = df2["Date"].str[:16]
                df2 = df2.drop(columns=["original_code","orig_complexity_score","rw_complexity_score"],errors="ignore")
                cols_order = ["Date","Language","Bugs","Security","Perf %","Confidence %","Complexity",
                              "Time O(·) Before","Time O(·) After","Space O(·) Before","Space O(·) After"]
                df2 = df2[[c for c in cols_order if c in df2.columns]]
                st.dataframe(df2, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    #  TIMELINE — CODE TIME TRAVELER
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Timeline":
        from ai_engine import time_travel_code

        ERAS = [
            ("1995", "🖥️",  "1995",    "Dawn Era"),
            ("2000", "💾",  "2000",    "Y2K"),
            ("2005", "🌐",  "2005",    "Web 2.0"),
            ("2010", "📱",  "2010",    "Smartphone"),
            ("2015", "⚡",  "2015",    "Modern"),
            ("today","🚀",  "2024",    "Today"),
            ("2030", "🤖",  "2030",    "AI-Native"),
            ("2040", "🌌",  "2040",    "Post-AGI"),
        ]

        st.markdown('<div class="pg-title">⏳ Code Time Traveler</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">See how your code would look across different eras of programming history — from the dawn of the web to a speculative AI-native future.</div>', unsafe_allow_html=True)

        col_left, col_right = st.columns([1.1, 0.9], gap="large")

        with col_left:
            tl_lang = st.selectbox("Language", LANGUAGES, key="tl_lang_sel")
            st.session_state.timeline_lang = tl_lang

            ide_header(tl_lang, "Paste Your Code")
            tl_code = st.text_area(
                "tl_code", height=280, key="tl_code_input", label_visibility="collapsed",
                placeholder=f"# Paste your {tl_lang} code here…\n# We'll rewrite it as if it was written in your chosen era!",
            )

            # Era selector grid
            st.markdown('<div class="tl-slider-container"><div style="font-size:0.72rem;font-weight:700;color:var(--mt);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.6rem;">Select Era</div>', unsafe_allow_html=True)

            selected_era = st.session_state.get("timeline_era", "2010")
            era_cols = st.columns(len(ERAS))
            for i, (era_key, icon, year, label) in enumerate(ERAS):
                with era_cols[i]:
                    is_spec = era_key in ("2030","2040")
                    is_active = selected_era == era_key
                    active_style = "border:2px solid var(--p1);background:rgba(99,102,241,0.15);color:var(--p1);" if is_active else "border:1.5px solid var(--bd);background:var(--sf2);color:var(--mt);"
                    spec_style  = "opacity:0.8;" if is_spec else ""
                    st.markdown(f"""
                    <div style="text-align:center;border-radius:10px;padding:0.45rem 0.3rem;{active_style}{spec_style}cursor:pointer;">
                      <div style="font-size:1.3rem;">{icon}</div>
                      <div style="font-size:0.65rem;font-weight:800;margin-top:0.1rem;">{year}</div>
                      <div style="font-size:0.55rem;opacity:0.7;">{label}</div>
                      {'<div style="font-size:0.5rem;color:#F59E0B;font-weight:700;">SPEC</div>' if is_spec else ''}
                    </div>""", unsafe_allow_html=True)
                    if st.button(icon, key=f"era_sel_{era_key}", use_container_width=True, help=f"Travel to {year}"):
                        st.session_state.timeline_era = era_key
                        st.session_state.timeline_result = None
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            era_key   = st.session_state.get("timeline_era", "2010")
            era_label = next((f"{icon} {year} — {lbl}" for k,icon,year,lbl in ERAS if k==era_key), era_key)
            st.markdown(f'<div class="tl-era-pill">{era_label}</div>', unsafe_allow_html=True)

            if era_key in ("2030","2040"):
                st.markdown('<div class="msg-warn">⚠️ Speculative / Science-Fiction mode — output is creative, not literal.</div>', unsafe_allow_html=True)

            tl_btn = st.button("⏳ Time Travel Code", key="btn_tl", use_container_width=True, type="primary")

        with col_right:
            # Info panel before run
            if not st.session_state.timeline_result:
                st.markdown("""
                <div class="panel">
                  <div class="panel-hdr">🕰️ HOW IT WORKS</div>
                  <div style="font-size:0.81rem;color:var(--tx2);line-height:1.75;">
                    <b style="color:var(--tx);">1. Paste your code</b> — any language, any complexity.<br><br>
                    <b style="color:var(--tx);">2. Pick an era</b> — from 1995's procedural dawn to 2040's fictional AI-native future.<br><br>
                    <b style="color:var(--tx);">3. Hit Time Travel</b> — the AI rewrites your code using the idioms, libraries, and patterns of that era.<br><br>
                    <b style="color:var(--tx);">4. Learn & compare</b> — see what changed, why, and what was the norm back then.
                  </div>
                </div>
                <div class="tl-fact-box">
                  <div class="tl-fact-title">✨ What makes each era unique</div>
                  <div class="tl-fact-item">🖥️ <span><b>1995–2000:</b> Manual memory, procedural code, no modern OOP</span></div>
                  <div class="tl-fact-item">🌐 <span><b>2005–2010:</b> Python 2, jQuery, callbacks, early AJAX</span></div>
                  <div class="tl-fact-item">⚡ <span><b>2015:</b> ES6 just landed, Python 3 emerging, React new</span></div>
                  <div class="tl-fact-item">🚀 <span><b>2024:</b> Type hints, async/await, modern best practices</span></div>
                  <div class="tl-fact-item">🤖 <span><b>2030–2040:</b> Speculative fiction — AI-native, intent-driven</span></div>
                </div>
                """, unsafe_allow_html=True)

        # ── Run time travel ──
        if tl_btn:
            if not tl_code.strip():
                st.warning("Please paste some code first!")
            elif not st.session_state.api_key:
                st.error("Please enter your Groq API key in the sidebar.")
            else:
                with st.spinner(f"⏳ Traveling to {era_label}…"):
                    result = time_travel_code(
                        st.session_state.api_key,
                        tl_code.strip(),
                        tl_lang,
                        era_key,
                    )
                st.session_state.timeline_result = result
                st.session_state.timeline_lang   = tl_lang
                st.rerun()

        # ── Display results ──
        if st.session_state.timeline_result:
            res  = st.session_state.timeline_result
            icon = res.get("era_icon", "⏳")
            spec = era_key in ("2030","2040")

            st.divider()
            st.markdown(f"""
            <div class="tl-result-header">
              <div class="tl-era-big-icon">{icon}</div>
              <div>
                <div class="tl-era-title">{res.get('era_label','')}{' <span class="speculative-badge">SPECULATIVE</span>' if spec else ''}</div>
                <div class="tl-era-subtitle">{res.get('era_summary','')}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Scores row
            rd  = int(res.get("readability_score", 50))
            nos = int(res.get("nostalgia_factor",   50))
            st.markdown(f"""
            <div class="tl-score-row">
              <div class="tl-score-card">
                <div class="tl-score-val">{rd}%</div>
                <div class="tl-score-label">Readability Today</div>
              </div>
              <div class="tl-score-card">
                <div class="tl-score-val">{nos}%</div>
                <div class="tl-score-label">Nostalgia Factor</div>
              </div>
              <div class="tl-score-card">
                <div class="tl-score-val">{len(res.get('changes',[]))}</div>
                <div class="tl-score-label">Changes Made</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Readability bar
            st.markdown(f"""
            <div class="tl-diff-bar">
              <span class="tl-diff-label">Readability</span>
              <div class="tl-diff-track"><div class="tl-diff-fill" style="width:{rd}%;"></div></div>
              <span style="font-size:0.72rem;font-weight:700;color:var(--p1);min-width:34px;">{rd}%</span>
            </div>
            <div class="tl-diff-bar">
              <span class="tl-diff-label">Nostalgia</span>
              <div class="tl-diff-track"><div class="tl-diff-fill" style="width:{nos}%;background:linear-gradient(90deg,#F59E0B,#EF4444);"></div></div>
              <span style="font-size:0.72rem;font-weight:700;color:#F59E0B;min-width:34px;">{nos}%</span>
            </div>
            """, unsafe_allow_html=True)

            # Era'd code
            tl_c1, tl_c2 = st.columns(2, gap="medium")
            with tl_c1:
                st.markdown(f'<div class="panel-hdr">📄 YOUR ORIGINAL CODE</div>', unsafe_allow_html=True)
                st.code(tl_code.strip(), language=st.session_state.timeline_lang.lower())
            with tl_c2:
                st.markdown(f'<div class="panel-hdr">{icon} CODE IN {era_label}</div>', unsafe_allow_html=True)
                era_code = res.get("era_code","")
                st.code(era_code, language=st.session_state.timeline_lang.lower())
                st.download_button(
                    f"⬇️ Download {era_label} Version",
                    data=era_code,
                    file_name=f"code_{era_key}.{st.session_state.timeline_lang.lower()[:3]}",
                    mime="text/plain",
                    use_container_width=True,
                )

            # Complexity note
            if res.get("complexity_note"):
                st.markdown(f'<div class="summary-box"><div class="summary-label">⚙️ Complexity Thinking in This Era</div><div class="summary-text">{res["complexity_note"]}</div></div>', unsafe_allow_html=True)

            # Changes
            changes = res.get("changes", [])
            if changes:
                st.markdown('<div class="panel-hdr">🔄 WHAT CHANGED & WHY</div>', unsafe_allow_html=True)
                for ch in changes:
                    st.markdown(f"""
                    <div class="tl-change-item">
                      <div class="tl-change-what">🔸 {ch.get('what','')}</div>
                      <div class="tl-change-why">{ch.get('why','')}</div>
                      <div class="tl-change-modern">→ Modern equivalent: {ch.get('modern_equivalent','')}</div>
                    </div>""", unsafe_allow_html=True)

            # Fun facts
            facts = res.get("fun_facts", [])
            if facts:
                facts_html = "".join(f'<div class="tl-fact-item">📌 <span>{f}</span></div>' for f in facts)
                st.markdown(f'<div class="tl-fact-box"><div class="tl-fact-title">📅 FUN FACTS FROM THIS ERA</div>{facts_html}</div>', unsafe_allow_html=True)

            # Try another era
            if st.button("🔄 Try Another Era", key="btn_tl_reset", use_container_width=True):
                st.session_state.timeline_result = None
                st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  CODE DNA
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Code DNA":
        from ai_engine import analyze_code_dna

        st.markdown('<div class="pg-title">🧬 Code DNA</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Your code has a fingerprint. Discover your developer archetype, superpowers, blind spots, and coding personality — all backed by real evidence from your code.</div>', unsafe_allow_html=True)

        dna_c1, dna_c2 = st.columns([1.1, 0.9], gap="large")

        with dna_c1:
            dna_lang = st.selectbox("Language", LANGUAGES, key="dna_lang_sel")
            ide_header(dna_lang, "Paste Your Code")
            dna_code = st.text_area(
                "dna_code", height=320, key="dna_code_input", label_visibility="collapsed",
                placeholder=f"# Paste your {dna_lang} code here…\n# The more code, the more accurate your DNA profile!\n# Try a full module or class for best results.",
            )
            n = len(dna_code)
            cls = "danger" if n > 8000 else "warn" if n > 5000 else ""
            st.markdown(f'<div class="char-cnt {cls}">{n:,} chars · Tip: paste 50+ lines for a richer profile</div>', unsafe_allow_html=True)
            dna_btn = st.button("🧬 Analyze My DNA", key="btn_dna", use_container_width=True, type="primary")

        with dna_c2:
            if not st.session_state.dna_result:
                st.markdown("""
                <div class="panel">
                  <div class="panel-hdr">🧬 WHAT IS CODE DNA?</div>
                  <div style="font-size:0.81rem;color:var(--tx2);line-height:1.8;">
                    Every developer has an unconscious coding style — patterns baked into how they name variables, handle errors, structure logic, and comment their work.<br><br>
                    Code DNA scans your code and reveals your <b style="color:var(--tx);">Developer Archetype</b>, your <b style="color:#10B981;">Superpowers</b>, your <b style="color:#EF4444;">Blind Spots</b>, and even which famous developer you code like.
                  </div>
                </div>
                <div class="panel">
                  <div class="panel-hdr">🏆 THE 8 ARCHETYPES</div>
                  <div style="font-size:0.79rem;color:var(--tx2);line-height:1.9;">
                    🏰 <b style="color:var(--tx);">Defensive Architect</b> — Guards every edge case<br>
                    ⚡ <b style="color:var(--tx);">Speed Demon</b> — Ships fast, fixes later<br>
                    🔬 <b style="color:var(--tx);">Perfectionist</b> — Every detail matters<br>
                    🔧 <b style="color:var(--tx);">Pragmatist</b> — Gets it done, balanced<br>
                    🎓 <b style="color:var(--tx);">Academic</b> — Theory-first, pattern-heavy<br>
                    🤠 <b style="color:var(--tx);">Cowboy</b> — No rules, raw instinct<br>
                    🪶 <b style="color:var(--tx);">Minimalist</b> — Less is always more<br>
                    🏗️ <b style="color:var(--tx);">Over-Engineer</b> — Built for scale on day one
                  </div>
                </div>
                """, unsafe_allow_html=True)

        if dna_btn:
            if not dna_code.strip():
                st.warning("Please paste some code first!")
            elif not st.session_state.api_key:
                st.error("Please enter your Groq API key in the sidebar.")
            else:
                with st.spinner("🧬 Sequencing your Code DNA…"):
                    result = analyze_code_dna(st.session_state.api_key, dna_code.strip(), dna_lang)
                st.session_state.dna_result = result
                st.session_state.dna_lang   = dna_lang
                st.rerun()

        if st.session_state.dna_result:
            dna = st.session_state.dna_result
            st.divider()

            r1, r2, r3 = st.columns([1, 1, 1], gap="medium")

            with r1:
                icon = dna.get("archetype_icon","🧬")
                arch = dna.get("archetype","The Pragmatist")
                desc = dna.get("archetype_desc","")
                st.markdown(f"""
                <div class="dna-archetype-card">
                  <span class="dna-archetype-icon">{icon}</span>
                  <div class="dna-archetype-name">{arch}</div>
                  <div class="dna-archetype-sub">{desc}</div>
                </div>""", unsafe_allow_html=True)

            with r2:
                score = int(dna.get("dna_score", 60))
                st.markdown(f"""
                <div class="panel" style="text-align:center;">
                  <div class="panel-hdr">🧪 DNA QUALITY SCORE</div>
                  <div class="dna-score-ring" style="--pct:{score};">
                    <div class="dna-score-val">{score}</div>
                  </div>
                  <div style="font-size:0.72rem;color:var(--mt);margin-top:0.3rem;">out of 100</div>
                  <div style="margin-top:0.8rem;font-size:0.8rem;color:var(--tx2);line-height:1.6;">{dna.get("summary","")}</div>
                </div>""", unsafe_allow_html=True)

            with r3:
                famous = dna.get("famous_developer_match","")
                works  = dna.get("works_well_with","")
                clashes= dna.get("clashes_with","")
                tags   = dna.get("compatibility_tags",[])
                tags_html = "".join(f'<span class="dna-compat-tag">{t}</span>' for t in tags)
                st.markdown(f"""
                <div class="panel">
                  <div class="panel-hdr">🤝 COMPATIBILITY</div>
                  <div style="font-size:0.72rem;color:var(--mt);margin-bottom:0.3rem;font-weight:700;">TAGS</div>
                  <div style="margin-bottom:0.7rem;">{tags_html}</div>
                  <div style="font-size:0.75rem;color:var(--tx2);margin-bottom:0.25rem;">✅ <b style="color:var(--tx);">Works well with:</b> {works}</div>
                  <div style="font-size:0.75rem;color:var(--tx2);">⚡ <b style="color:var(--tx);">Clashes with:</b> {clashes}</div>
                </div>""", unsafe_allow_html=True)
                if famous:
                    st.markdown(f"""
                    <div class="dna-famous-box">
                      <div class="dna-famous-icon">👑</div>
                      <div>
                        <div class="dna-famous-label">You code like</div>
                        <div class="dna-famous-name">{famous}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

            # Gene strands
            genes = dna.get("genes", [])
            if genes:
                st.markdown('<div class="panel"><div class="panel-hdr">🔬 YOUR CODING GENES</div>', unsafe_allow_html=True)

                GENE_COLORS = [
                    "linear-gradient(90deg,#6366F1,#8B5CF6)",
                    "linear-gradient(90deg,#06B6D4,#0891B2)",
                    "linear-gradient(90deg,#10B981,#059669)",
                    "linear-gradient(90deg,#F59E0B,#D97706)",
                    "linear-gradient(90deg,#F43F5E,#E11D48)",
                    "linear-gradient(90deg,#8B5CF6,#6366F1)",
                    "linear-gradient(90deg,#22D3EE,#06B6D4)",
                ]
                for i, gene in enumerate(genes):
                    score_g = int(gene.get("score", 50))
                    color   = GENE_COLORS[i % len(GENE_COLORS)]
                    evidence= gene.get("evidence","")
                    st.markdown(f"""
                    <div class="dna-gene-row">
                      <div class="dna-gene-name">{gene.get('trait','')}</div>
                      <div class="dna-gene-track">
                        <div class="dna-gene-fill" style="width:{score_g}%;background:{color};"></div>
                      </div>
                      <div class="dna-gene-label">{gene.get('label','')}</div>
                    </div>""", unsafe_allow_html=True)
                    if evidence:
                        st.markdown(f'<div style="font-size:0.68rem;color:var(--mt);padding:0 0 0.4rem 0;font-style:italic;">Evidence: {evidence}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Superpowers and blind spots
            pw_col, bl_col = st.columns(2, gap="medium")
            with pw_col:
                powers = dna.get("superpowers", [])
                st.markdown('<div class="panel-hdr">⚡ YOUR SUPERPOWERS</div>', unsafe_allow_html=True)
                for p in powers:
                    st.markdown(f"""
                    <div class="dna-power-card">
                      <div class="dna-power-title">{p.get('icon','✨')} {p.get('title','')}</div>
                      <div class="dna-power-desc">{p.get('desc','')}</div>
                    </div>""", unsafe_allow_html=True)

            with bl_col:
                blinds = dna.get("blind_spots", [])
                st.markdown('<div class="panel-hdr">🕳️ YOUR BLIND SPOTS</div>', unsafe_allow_html=True)
                for b in blinds:
                    st.markdown(f"""
                    <div class="dna-blind-card">
                      <div class="dna-blind-title">{b.get('icon','⚠️')} {b.get('title','')}</div>
                      <div class="dna-blind-desc">{b.get('desc','')}</div>
                    </div>""", unsafe_allow_html=True)

            if st.button("🔄 Analyze Different Code", key="btn_dna_reset", use_container_width=True):
                st.session_state.dna_result = None
                st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  CODE INTERVIEW SIMULATOR
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Interview":
        from ai_engine import interview_ask

        TOTAL_QUESTIONS = 5

        st.markdown('<div class="pg-title">🎤 Code Interview Simulator</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">A senior FAANG engineer interviews you live about your own code. Every answer is scored strictly based on whether it actually addresses the question. Irrelevant answers get low scores.</div>', unsafe_allow_html=True)

        # ── Setup phase ──
        if not st.session_state.interview_current and not st.session_state.interview_done:
            if not st.session_state.interview_history:
                iv_c1, iv_c2 = st.columns([1.2, 0.8], gap="large")
                with iv_c1:
                    iv_lang = st.selectbox("Language", LANGUAGES, key="iv_lang_sel")
                    ide_header(iv_lang, "Paste the Code You Want to Be Interviewed On")
                    iv_code_input = st.text_area(
                        "iv_code", height=300, key="iv_code_input", label_visibility="collapsed",
                        placeholder=f"# Paste any {iv_lang} code here…\n# The interviewer will ask 5 specific questions about YOUR code.\n# Use real code you wrote for the most authentic experience!",
                    )
                    n = len(iv_code_input)
                    cls = "danger" if n > 8000 else "warn" if n > 5000 else ""
                    st.markdown(f'<div class="char-cnt {cls}">{n:,} chars</div>', unsafe_allow_html=True)
                    start_btn = st.button("🎤 Start Interview", key="btn_iv_start", use_container_width=True, type="primary")

                with iv_c2:
                    st.markdown("""
                    <div class="panel">
                      <div class="panel-hdr">🏢 HOW IT WORKS</div>
                      <div style="font-size:0.81rem;color:var(--tx2);line-height:1.85;">
                        <b style="color:var(--tx);">1. Paste your code</b> — real code gives the most realistic interview.<br><br>
                        <b style="color:var(--tx);">2. The interviewer asks</b> — specific questions about your actual code, referencing real function/variable names.<br><br>
                        <b style="color:var(--tx);">3. You answer</b> — each answer is scored strictly: off-topic answers score 0–20.<br><br>
                        <b style="color:var(--tx);">4. 5 questions deep</b> — difficulty adapts to your answers.<br><br>
                        <b style="color:var(--tx);">5. Honest verdict</b> — Strong Hire / Hire / No Hire / Strong No Hire based on your actual performance.
                      </div>
                    </div>
                    <div class="panel">
                      <div class="panel-hdr">📊 HOW SCORES WORK</div>
                      <div style="font-size:0.79rem;color:var(--tx2);line-height:1.95;">
                        <span style="color:#EF4444;font-weight:700;">0–20</span> — Answer doesn't address the question<br>
                        <span style="color:#F97316;font-weight:700;">21–35</span> — Vague, no technical substance<br>
                        <span style="color:#F59E0B;font-weight:700;">36–55</span> — Partially addresses the question<br>
                        <span style="color:#10B981;font-weight:700;">56–75</span> — Correctly addresses with good reasoning<br>
                        <span style="color:#6366F1;font-weight:700;">76–95</span> — Excellent: thorough with tradeoffs
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                if start_btn:
                    if not iv_code_input.strip():
                        st.warning("Please paste some code first!")
                    elif not st.session_state.api_key:
                        st.error("Please enter your Groq API key in the sidebar.")
                    else:
                        with st.spinner("🎤 Your interviewer is reviewing your code…"):
                            result = interview_ask(
                                st.session_state.api_key,
                                iv_code_input.strip(),
                                iv_lang,
                                [],
                            )
                        st.session_state.interview_code    = iv_code_input.strip()
                        st.session_state.interview_lang    = iv_lang
                        st.session_state.interview_current = result
                        st.session_state.interview_history = []
                        st.session_state.interview_scores  = []
                        st.session_state.interview_done    = False
                        st.rerun()
            return

        # Ensure scores list exists
        if "interview_scores" not in st.session_state:
            st.session_state.interview_scores = []

        # ── Active interview ──
        if st.session_state.interview_current and not st.session_state.interview_done:
            cur     = st.session_state.interview_current
            stage   = int(cur.get("stage", 1))
            history = st.session_state.interview_history
            scores  = st.session_state.interview_scores

            # Progress stepper
            prog_html = ""
            for i in range(1, TOTAL_QUESTIONS + 2):
                if i < stage:
                    s_val = scores[i-1] if i-1 < len(scores) else 0
                    s_color = "#10B981" if s_val >= 60 else "#F59E0B" if s_val >= 35 else "#EF4444"
                    cls = "done"; lbl = "✓"
                elif i == stage:
                    cls = "active"; lbl = str(i)
                else:
                    cls = ""; lbl = str(i)
                prog_html += f'<div class="iv-step {cls}">{lbl}</div>'
                if i <= TOTAL_QUESTIONS:
                    line_cls = "done" if i < stage else ""
                    prog_html += f'<div class="iv-step-line {line_cls}"></div>'

            # Running score display
            running_avg = round(sum(scores) / len(scores)) if scores else 0
            sc_color = "#10B981" if running_avg >= 60 else "#F59E0B" if running_avg >= 35 else "#EF4444"

            st.markdown(f"""
            <div class="iv-header">
              <div class="iv-header-icon">🎤</div>
              <div style="flex:1;">
                <div class="iv-company-badge">🏢 FAANG-Level Interview</div>
                <div class="iv-title">Technical Interview in Progress</div>
                <div class="iv-sub">Question {stage} of {TOTAL_QUESTIONS} · {st.session_state.interview_lang}</div>
              </div>
              {f'<div style="text-align:center;"><div style="font-size:1.8rem;font-weight:900;color:{sc_color};">{running_avg}</div><div style="font-size:0.62rem;color:var(--mt);text-transform:uppercase;letter-spacing:1.5px;">Running Score</div></div>' if scores else ''}
            </div>
            <div class="iv-progress-row">{prog_html}</div>
            """, unsafe_allow_html=True)

            # Previous Q&A with scores
            if history and scores:
                with st.expander(f"📜 Interview History — {len(scores)} answer(s) scored", expanded=False):
                    q_msgs = [m for m in history if m["role"] == "assistant"]
                    a_msgs = [m for m in history if m["role"] == "user"]
                    for i, (qm, am) in enumerate(zip(q_msgs, a_msgs)):
                        s = scores[i] if i < len(scores) else 0
                        s_col = "#10B981" if s >= 60 else "#F59E0B" if s >= 35 else "#EF4444"
                        st.markdown(f"""
                        <div style="margin-bottom:0.8rem;padding:0.6rem 0.8rem;background:var(--sf2);border-radius:8px;border:1px solid var(--bd);">
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">
                            <span style="color:var(--p1);font-weight:700;font-size:0.78rem;">Q{i+1}: {qm['content'][:120]}{'…' if len(qm['content'])>120 else ''}</span>
                            <span style="font-size:0.82rem;font-weight:800;color:{s_col};min-width:36px;text-align:right;">{s}/100</span>
                          </div>
                          <div style="font-size:0.75rem;color:var(--tx2);padding-left:0.5rem;">You: {am['content'][:150]}{'…' if len(am['content'])>150 else ''}</div>
                        </div>""", unsafe_allow_html=True)

            # Show evaluation of previous answer (with score)
            if cur.get("evaluation") and history:
                ans_score = int(cur.get("answer_score", 0))
                s_col = "#10B981" if ans_score >= 60 else "#F59E0B" if ans_score >= 35 else "#EF4444"
                st.markdown(f"""
                <div class="iv-eval-box">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
                    <strong>Interviewer's evaluation of your last answer:</strong>
                    <span style="font-size:1.1rem;font-weight:900;color:{s_col};">{ans_score}/100</span>
                  </div>
                  {cur["evaluation"]}
                </div>""", unsafe_allow_html=True)

            # Current question
            diff     = cur.get("difficulty","medium")
            diff_cls = f"iv-q-{diff}"
            focus    = cur.get("focus_area","General")
            hint     = cur.get("hint","")
            question = cur.get("question","")
            q_context= cur.get("question_context","")

            st.markdown(f"""
            <div class="iv-question-card">
              <div class="iv-q-meta">
                <span class="iv-q-badge {diff_cls}">{diff.upper()}</span>
                <span class="iv-q-focus">🎯 {focus}</span>
                {f'<span style="font-size:0.63rem;color:var(--mt);">about: <b>{q_context}</b></span>' if q_context else ''}
                <span style="font-size:0.65rem;color:var(--mt);margin-left:auto;">Q{stage} of {TOTAL_QUESTIONS}</span>
              </div>
              <div class="iv-q-text">{question}</div>
              {f'<div class="iv-hint-box">💡 Hint: {hint}</div>' if hint else ''}
            </div>
            """, unsafe_allow_html=True)

            answer = st.text_area(
                "Your Answer", height=160, key=f"iv_answer_{stage}",
                placeholder="Answer specifically about the code element mentioned in the question. Vague or off-topic answers will score 0–20.",
            )

            iv_col1, iv_col2 = st.columns([2,1])
            with iv_col1:
                submit_btn = st.button(
                    "Submit Answer →" if stage < TOTAL_QUESTIONS else "Submit Final Answer →",
                    key=f"btn_iv_submit_{stage}", use_container_width=True, type="primary"
                )
            with iv_col2:
                if st.button("🚪 End Interview", key=f"btn_iv_end_{stage}", use_container_width=True):
                    st.session_state.interview_done    = True
                    st.session_state.interview_current = None
                    st.rerun()

            if submit_btn:
                if not answer.strip():
                    st.warning("Please type your answer before submitting.")
                else:
                    new_history = history + [
                        {"role": "assistant", "content": question},
                        {"role": "user",      "content": answer.strip()},
                    ]
                    with st.spinner("🤔 Evaluating your answer strictly…"):
                        next_q = interview_ask(
                            st.session_state.api_key,
                            st.session_state.interview_code,
                            st.session_state.interview_lang,
                            new_history,
                            answer.strip(),
                        )

                    # Record the per-answer score
                    ans_score = int(next_q.get("answer_score", 0))
                    new_scores = st.session_state.interview_scores + [ans_score]
                    st.session_state.interview_scores  = new_scores
                    st.session_state.interview_history = new_history

                    is_final = (stage >= TOTAL_QUESTIONS) or (next_q.get("verdict","in_progress") != "in_progress")

                    if is_final:
                        # Compute honest cumulative score from all recorded per-answer scores
                        honest_avg = round(sum(new_scores) / len(new_scores)) if new_scores else 0
                        next_q["cumulative_score"] = honest_avg
                        # Override verdict based on honest average
                        if honest_avg >= 80:
                            next_q["verdict"] = "strong_hire"
                        elif honest_avg >= 60:
                            next_q["verdict"] = "hire"
                        elif honest_avg >= 35:
                            next_q["verdict"] = "no_hire"
                        else:
                            next_q["verdict"] = "strong_no_hire"
                        st.session_state.interview_current = next_q
                        st.session_state.interview_done    = True
                    else:
                        st.session_state.interview_current = next_q
                    st.rerun()

        # ── Final verdict ──
        if st.session_state.interview_done:
            cur    = st.session_state.interview_current or {}
            scores = st.session_state.get("interview_scores", [])

            # Always use honest average from recorded scores
            if scores:
                honest_avg = round(sum(scores) / len(scores))
            else:
                honest_avg = int(cur.get("cumulative_score", 0))

            # Determine verdict from honest average
            if honest_avg >= 80:
                verdict = "strong_hire"
            elif honest_avg >= 60:
                verdict = "hire"
            elif honest_avg >= 35:
                verdict = "no_hire"
            else:
                verdict = "strong_no_hire"

            feedback     = cur.get("final_feedback","")
            strengths    = cur.get("strengths",[])
            improvements = cur.get("improvements",[])

            VERDICT_MAP = {
                "strong_hire":    ("🌟", "Strong Hire",    "verdict-strong-hire",    "#10B981"),
                "hire":           ("✅", "Hire",           "verdict-hire",           "#6366F1"),
                "no_hire":        ("⚠️", "No Hire",        "verdict-no-hire",        "#F59E0B"),
                "strong_no_hire": ("❌", "Strong No Hire", "verdict-strong-no-hire", "#EF4444"),
            }
            v_emoji, v_label, v_cls, v_color = VERDICT_MAP.get(verdict, VERDICT_MAP["no_hire"])

            st.markdown(f"""
            <div class="iv-verdict-card {v_cls}">
              <div class="iv-verdict-emoji">{v_emoji}</div>
              <div class="iv-verdict-label" style="color:{v_color};">{v_label}</div>
              <div class="iv-score-big" style="color:{v_color};">{honest_avg}</div>
              <div class="iv-score-sub">Average Score Across {len(scores)} Answers</div>
            </div>
            """, unsafe_allow_html=True)

            # Per-question score breakdown
            if scores:
                st.markdown('<div class="panel"><div class="panel-hdr">📊 PER-ANSWER SCORE BREAKDOWN</div>', unsafe_allow_html=True)
                history = st.session_state.interview_history
                q_msgs  = [m for m in history if m["role"] == "assistant"]
                a_msgs  = [m for m in history if m["role"] == "user"]
                for i, s in enumerate(scores):
                    s_col  = "#10B981" if s >= 60 else "#F59E0B" if s >= 35 else "#EF4444"
                    q_text = q_msgs[i]["content"][:100] + "…" if i < len(q_msgs) and len(q_msgs[i]["content"]) > 100 else (q_msgs[i]["content"] if i < len(q_msgs) else f"Question {i+1}")
                    a_text = a_msgs[i]["content"][:100] + "…" if i < len(a_msgs) and len(a_msgs[i]["content"]) > 100 else (a_msgs[i]["content"] if i < len(a_msgs) else "—")
                    bar_w  = s
                    st.markdown(f"""
                    <div style="margin-bottom:0.7rem;padding:0.65rem 0.9rem;background:var(--sf2);border-radius:10px;border:1px solid var(--bd);">
                      <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                        <span style="font-size:0.78rem;color:var(--tx);font-weight:700;">Q{i+1}: {q_text}</span>
                        <span style="font-size:0.92rem;font-weight:900;color:{s_col};">{s}/100</span>
                      </div>
                      <div style="height:5px;background:var(--bd);border-radius:3px;margin-bottom:0.3rem;overflow:hidden;">
                        <div style="height:100%;width:{bar_w}%;background:{s_col};border-radius:3px;"></div>
                      </div>
                      <div style="font-size:0.71rem;color:var(--mt);">Your answer: {a_text}</div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if feedback:
                st.markdown(f'<div class="summary-box"><div class="summary-label">📋 Final Interviewer Feedback</div><div class="summary-text">{feedback}</div></div>', unsafe_allow_html=True)

            fb_c1, fb_c2 = st.columns(2, gap="medium")
            with fb_c1:
                if strengths:
                    st.markdown('<div class="panel"><div class="panel-hdr">⚡ YOUR STRENGTHS</div>', unsafe_allow_html=True)
                    for s in strengths:
                        st.markdown(f'<div style="padding:0.42rem 0;border-bottom:1px solid var(--bd);font-size:0.82rem;color:var(--tx2);display:flex;gap:0.5rem;align-items:flex-start;">✅ <span>{s}</span></div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            with fb_c2:
                if improvements:
                    st.markdown('<div class="panel"><div class="panel-hdr">🎯 AREAS TO IMPROVE</div>', unsafe_allow_html=True)
                    for imp in improvements:
                        st.markdown(f'<div style="padding:0.42rem 0;border-bottom:1px solid var(--bd);font-size:0.82rem;color:var(--tx2);display:flex;gap:0.5rem;align-items:flex-start;">📌 <span>{imp}</span></div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🔄 Start New Interview", key="btn_iv_restart", use_container_width=True, type="primary"):
                st.session_state.interview_code    = ""
                st.session_state.interview_lang    = "Python"
                st.session_state.interview_history = []
                st.session_state.interview_current = None
                st.session_state.interview_done    = False
                st.session_state.interview_scores  = []
                st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  SETTINGS
    # ════════════════════════════════════════════════════════════════════════
    elif nav_key == "Settings":
        st.markdown('<div class="pg-title">Settings</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Customize your CodeRefine experience.</div>', unsafe_allow_html=True)

        s1, s2 = st.columns(2, gap="large")

        with s1:
            st.markdown('<div class="panel"><div class="panel-hdr">🎨 APPEARANCE</div>', unsafe_allow_html=True)

            # Theme picker
            st.markdown('<div style="font-size:0.74rem;color:var(--tx2);font-weight:600;margin-bottom:0.5rem;">Theme</div>', unsafe_allow_html=True)
            theme_info = {
                "dark":     ("#0D1323", "Dark",     "🌑"),
                "midnight": ("#020408", "Midnight",  "🌌"),
                "slate":    ("#1E293B", "Slate",     "🪨"),
                "light":    ("#F8FAFC", "Light",     "☀️"),
                "warm":     ("#FEFCE8", "Warm",      "🌤️"),
            }
            th_cols = st.columns(5)
            for col, (key, (color, label, icon)) in zip(th_cols, theme_info.items()):
                with col:
                    is_sel = st.session_state.theme == key
                    border_style = f"3px solid var(--p1)" if is_sel else "2px solid var(--bd)"
                    st.markdown(f"""
                    <div style="text-align:center;cursor:pointer;" title="{label}">
                      <div style="width:44px;height:44px;border-radius:10px;background:{color};
                                  border:{border_style};margin:0 auto 0.3rem;
                                  box-shadow:{'0 0 0 3px var(--glow)' if is_sel else 'none'};
                                  display:flex;align-items:center;justify-content:center;
                                  font-size:1.2rem;">{icon}</div>
                      <div style="font-size:0.62rem;color:{'var(--p1)' if is_sel else 'var(--mt)'};font-weight:{'700' if is_sel else '500'};">{label}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("  ", key=f"th_{key}", use_container_width=True):
                        st.session_state.theme = key

            # Accent color picker
            st.markdown('<div style="font-size:0.74rem;color:var(--tx2);font-weight:600;margin:1.1rem 0 0.5rem;">Accent Color</div>', unsafe_allow_html=True)
            acc_info = {
                "indigo":  ("#6366F1", "Indigo"),
                "cyan":    ("#06B6D4", "Cyan"),
                "emerald": ("#10B981", "Emerald"),
                "rose":    ("#F43F5E", "Rose"),
                "amber":   ("#F59E0B", "Amber"),
            }
            ac_cols = st.columns(5)
            for col, (key, (color, label)) in zip(ac_cols, acc_info.items()):
                with col:
                    is_sel = st.session_state.accent == key
                    st.markdown(f"""
                    <div style="text-align:center;" title="{label}">
                      <div style="width:36px;height:36px;border-radius:50%;background:{color};
                                  border:{'3px solid var(--tx)' if is_sel else '2px solid transparent'};
                                  margin:0 auto 0.28rem;
                                  box-shadow:{'0 0 0 3px ' + color + '40' if is_sel else 'none'};"></div>
                      <div style="font-size:0.6rem;color:{'var(--tx)' if is_sel else 'var(--mt)'};font-weight:{'700' if is_sel else '400'};">{label}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button(" ", key=f"ac_{key}", use_container_width=True):
                        st.session_state.accent = key

            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("💾 Save Appearance", key="save_app", type="primary"):
                update_user_settings(user["id"], st.session_state.theme, st.session_state.accent)
                st.session_state.user["theme"]        = st.session_state.theme
                st.session_state.user["accent_color"] = st.session_state.accent
                st.success("✓ Saved!"); st.rerun()

        with s2:
            st.markdown('<div class="panel"><div class="panel-hdr">👤 ACCOUNT</div>', unsafe_allow_html=True)
            rows = [
                ("Username",      user["username"]),
                ("Email",         user.get("email","—")),
                ("Member since",  (user.get("created_at","")[:10]) or "—"),
                ("Total Reviews", str(tot_rev)),
                ("AI Model",      "llama-3.3-70b-versatile"),
                ("Provider",      "Groq Cloud"),
            ]
            for lbl, val in rows:
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:0.52rem 0;border-bottom:1px solid var(--bd);"><span style="color:var(--mt);font-size:0.81rem;">{lbl}</span><span style="color:var(--tx);font-weight:600;font-size:0.81rem;">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel"><div class="panel-hdr">🔒 PRIVACY</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.8rem;color:var(--tx2);line-height:1.7;">Your API key is stored only in your browser session — never on our servers.<br>The first 800 characters of your code are saved locally for analytics only.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ════════════════════════════════════════════════════════════════════════════════
inject_css()

if st.session_state.user and st.session_state.page != "dashboard":
    st.session_state.page = "dashboard"
if not st.session_state.user and st.session_state.page == "dashboard":
    st.session_state.page = "login"

_p = st.session_state.page
if _p == "login":
    page_login()
elif _p == "signup":
    page_signup()
else:
    page_dashboard()
