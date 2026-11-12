"""Injects the FixMate design system into Streamlit."""

from __future__ import annotations

import streamlit as st

from i18n import is_rtl
from phone_css import PHONE_FRAME, PHONE_RULES

from config import ASSETS_DIR


_STYLESHEETS = ("styles.css", "workspace.css", "app-pages.css", "candy.css", "fixes.css")


def _load_css() -> str:
    return "\n".join(
        (ASSETS_DIR / name).read_text(encoding="utf-8") for name in _STYLESHEETS
    )


_BACKGROUND = """
<div class="fm-bg" aria-hidden="true">
    <span class="fm-bg-blob fm-bg-blob-a"></span>
    <span class="fm-bg-blob fm-bg-blob-b"></span>
    <span class="fm-bg-blob fm-bg-blob-c"></span>
    <span class="fm-bg-line"></span>
</div>
"""


# Light mode flips the dark design (colours and brightness) and turns pictures back the right way up.
_LIGHT_MODE = """
<style>
html { filter: invert(1) hue-rotate(180deg); background: #0d1716; }
.fm-mascot { filter: invert(1) hue-rotate(180deg); }
img, video, [data-testid="stImage"] img { filter: invert(1) hue-rotate(180deg); }
</style>
"""


_RTL_MODE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;600;800&display=swap');
html, body, .stApp { direction: rtl; }
.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp button, .stApp input, .stApp textarea, .stApp [data-baseweb="select"] {
  font-family: 'Noto Sans Arabic', 'Archivo', sans-serif !important; letter-spacing: 0 !important;
}
.stApp .stMarkdown, .stApp label { text-align: right; }
.stApp input, .stApp textarea { direction: rtl; text-align: right; }
</style>
"""


# Each page gets its own pair of accent colours.
_PAGE_ACCENTS = {
    "home": ("#2dd4bf", "#38bdf8"),
    "diagnosis": ("#4ade80", "#2dd4bf"),
    "chat": ("#38bdf8", "#818cf8"),
    "dashboard": ("#818cf8", "#38bdf8"),
    "history": ("#fbbf24", "#4ade80"),
    "about": ("#2dd4bf", "#818cf8"),
}


def inject_styles() -> None:
    st.markdown(f"<style>{_load_css()}</style>", unsafe_allow_html=True)
    st.markdown(_BACKGROUND, unsafe_allow_html=True)
    if st.session_state.get("theme", "dark") == "light":
        st.markdown(_LIGHT_MODE, unsafe_allow_html=True)
    if is_rtl():
        st.markdown(_RTL_MODE, unsafe_allow_html=True)
    first, second = _PAGE_ACCENTS.get(st.session_state.get("page", "home"), _PAGE_ACCENTS["home"])
    st.markdown(f"<style>:root {{ --a1: {first}; --a2: {second}; }}</style>", unsafe_allow_html=True)
    view = st.session_state.get("view")
    if view == "phone":
        st.markdown(f"<style>{PHONE_RULES} {PHONE_FRAME}</style>", unsafe_allow_html=True)
    elif view != "laptop":
        st.markdown(f"<style>@media (max-width: 768px) {{ {PHONE_RULES} }}</style>", unsafe_allow_html=True)
