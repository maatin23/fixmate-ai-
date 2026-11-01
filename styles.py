"""Injects the FixMate design system into Streamlit."""

from __future__ import annotations

import streamlit as st

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


def inject_styles() -> None:
    st.markdown(f"<style>{_load_css()}</style>", unsafe_allow_html=True)
    st.markdown(_BACKGROUND, unsafe_allow_html=True)
