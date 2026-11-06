"""Injects the FixMate design system into Streamlit."""

from __future__ import annotations

import streamlit as st

from i18n import is_rtl

from config import ASSETS_DIR


_STYLESHEETS = ("styles.css", "workspace.css", "app-pages.css", "blueprint.css")


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
html { filter: invert(1) hue-rotate(180deg); background: #071033; }
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


def inject_styles() -> None:
    st.markdown(f"<style>{_load_css()}</style>", unsafe_allow_html=True)
    st.markdown(_BACKGROUND, unsafe_allow_html=True)
    if st.session_state.get("theme", "dark") == "light":
        st.markdown(_LIGHT_MODE, unsafe_allow_html=True)
    if is_rtl():
        st.markdown(_RTL_MODE, unsafe_allow_html=True)
