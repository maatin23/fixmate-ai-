"""Interface language support: English, Central Kurdish (Sorani) and Arabic."""

from __future__ import annotations

import html
import re

import streamlit as st

from i18n_data import AR, CKB

LANGS = {"en": "English", "ckb": "کوردی", "ar": "العربية"}
RTL_LANGS = {"ckb", "ar"}
_TABLES = {"ar": AR, "ckb": CKB}
_AI_NAMES = {
    "ar": "Arabic",
    "ckb": "Central Kurdish (Sorani), written in Arabic script, as spoken in Sulaymaniyah",
}
_NODE = re.compile(r">([^<>]+)<")


def current_lang() -> str:
    try:
        lang = st.session_state.get("lang", "en")
    except Exception:
        return "en"
    return lang if lang in LANGS else "en"


def is_rtl() -> bool:
    return current_lang() in RTL_LANGS


def t(text: str) -> str:
    """Translate one interface string; unknown strings stay in English."""
    table = _TABLES.get(current_lang())
    if not table:
        return text
    return table.get(" ".join(str(text).split()), text)


def translate_html(markup: str) -> str:
    """Translate the text between tags when an exact translation exists."""
    table = _TABLES.get(current_lang())
    if not table:
        return markup

    def replace(match: re.Match) -> str:
        key = " ".join(html.unescape(match.group(1)).split())
        translated = table.get(key)
        return ">" + html.escape(translated, quote=False) + "<" if translated else match.group(0)

    return _NODE.sub(replace, markup)


def language_name() -> str:
    """Language the AI should answer in ('' for English)."""
    return _AI_NAMES.get(current_lang(), "")
