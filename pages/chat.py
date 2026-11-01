"""Ask AI workspace page."""

from __future__ import annotations

import streamlit as st

from components.cards import page_header
from components.chat import render_chat


def render() -> None:
    with st.container(key="fm-chat-page"):
        page_header(
            "ASK AI WORKSPACE",
            "Keep the context. Ask better questions.",
            "Use this space to unpack a diagnosis, request simpler wording, or prepare the questions worth asking a technician. "
            "When a report is loaded, its findings and safety flags travel with the conversation.",
        )
        render_chat(st.session_state.get("current_diagnostic"), page_key="ask")
