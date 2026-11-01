"""Render trusted, pre-escaped HTML blocks without Markdown re-parsing."""

from __future__ import annotations

import streamlit as st


def compact_html(markup: str) -> str:
    """Keep block HTML on flush-left lines so Markdown never treats it as code."""
    lines = [line.strip() for line in str(markup).strip().splitlines()]
    return "\n".join(line for line in lines if line)


def html_block(markup: str) -> None:
    st.markdown(compact_html(markup), unsafe_allow_html=True)
