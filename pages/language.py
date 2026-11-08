"""Welcome page: choose the language and whether you are on a phone or a laptop."""

from __future__ import annotations

import streamlit as st

from components.icons import logo_mark
from components.render import html_block

_LANGS = [("en", "English"), ("ckb", "کوردی"), ("ar", "العربية")]
_VIEWS = [
    ("phone", "Phone · مۆبایل · هاتف", "smartphone"),
    ("laptop", "Laptop · لاپتۆپ · لابتوب", "laptop_mac"),
]


def _guess_view() -> str:
    """Pre-select Phone when the browser looks like a phone."""
    try:
        agent = (st.context.headers.get("User-Agent") or "").lower()
    except Exception:
        return "laptop"
    return "phone" if any(word in agent for word in ("iphone", "android", "mobile", "ipod")) else "laptop"


def _pick_lang(code: str) -> None:
    st.session_state.lang = code
    st.session_state.lang_picked = True


def _pick_view(code: str) -> None:
    st.session_state.view = code


def _continue() -> None:
    st.session_state.lang_chosen = True


def render() -> None:
    if st.session_state.get("view") is None:
        st.session_state.view = _guess_view()
    picked = bool(st.session_state.get("lang_picked"))

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
        for column, (code, label) in zip(st.columns(3), _LANGS):
            with column:
                st.button(
                    label,
                    key=f"lang_pick_{code}",
                    type="primary" if picked and st.session_state.get("lang") == code else "secondary",
                    on_click=_pick_lang,
                    args=(code,),
                    width="stretch",
                )
        html_block('<p class="fm-lang-sub fm-lang-sub-2">Choose your device · ئامێرەکەت هەڵبژێرە · اختر جهازك</p>')
        for column, (code, label, symbol) in zip(st.columns(2), _VIEWS):
            with column:
                st.button(
                    label,
                    key=f"view_pick_{code}",
                    icon=f":material/{symbol}:",
                    type="primary" if st.session_state.get("view") == code else "secondary",
                    on_click=_pick_view,
                    args=(code,),
                    width="stretch",
                )
        st.button(
            "Continue · بەردەوام بە · متابعة",
            key="lang_continue",
            type="primary",
            disabled=not picked,
            on_click=_continue,
            width="stretch",
        )
