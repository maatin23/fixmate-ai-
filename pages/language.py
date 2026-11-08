"""Welcome page that asks for the language the first time someone opens the app."""

from __future__ import annotations

import streamlit as st

from components.icons import logo_mark
from components.render import html_block

_CHOICES = [
    ("en", "English"),
    ("ckb", "کوردی"),
    ("ar", "العربية"),
]


def _pick(code: str) -> None:
    st.session_state.lang = code
    st.session_state.lang_chosen = True


def render() -> None:
    with st.container(key="lang-splash"):
        html_block(
            f"""
            <div class="fm-lang-head">
                {logo_mark(76)}
                <h1>FixMate AI</h1>
                <p class="fm-lang-sub">Choose your language · زمانەکەت هەڵبژێرە · اختر لغتك</p>
            </div>
            """
        )
        for column, (code, label) in zip(st.columns(3), _CHOICES):
            with column:
                st.button(label, key=f"lang_pick_{code}", on_click=_pick, args=(code,), width="stretch")
