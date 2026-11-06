"""Custom navigation and site footer."""

from __future__ import annotations

import streamlit as st

from components.icons import brand_lockup, icon
from components.render import html_block
from state import LABEL_TO_PAGE, begin_diagnosis

_NAV_ITEMS = ["Home", "Diagnose", "Dashboard", "History", "Ask AI", "About"]


def _on_nav_change() -> None:
    selected = st.session_state.get("nav_choice")
    page = LABEL_TO_PAGE.get(selected)
    if page:
        st.session_state.page = page


def _toggle_theme() -> None:
    st.session_state.theme = "light" if st.session_state.get("theme", "dark") == "dark" else "dark"


def render_navbar() -> None:
    current_page = st.session_state.get("page", "home")
    expected_label = next((label for label in _NAV_ITEMS if LABEL_TO_PAGE.get(label) == current_page), "Home")
    if st.session_state.get("nav_choice") != expected_label:
        st.session_state.nav_choice = expected_label

    with st.container(key="fm-navbar"):
        brand_col, nav_col, theme_col, cta_col = st.columns([2.6, 4.9, 1.5, 2.0], vertical_alignment="center")
        with brand_col:
            html_block(brand_lockup(38))
        with nav_col:
            st.radio(
                "Primary navigation",
                _NAV_ITEMS,
                key="nav_choice",
                horizontal=True,
                label_visibility="collapsed",
                on_change=_on_nav_change,
            )
        with theme_col:
            is_dark = st.session_state.get("theme", "dark") == "dark"
            st.button(
                "Light" if is_dark else "Dark",
                key="nav_theme_toggle",
                icon=":material/light_mode:" if is_dark else ":material/dark_mode:",
                width="stretch",
                on_click=_toggle_theme,
            )
        with cta_col:
            st.button(
                "Start diagnosis",
                key="nav_start_diagnosis",
                type="primary",
                width="stretch",
                on_click=begin_diagnosis,
                args=(),
            )


def render_footer() -> None:
    with st.container(key="fm-footer"):
        html_block(
            f"""
            <footer class="fm-footer">
                <div class="fm-footer-grid">
                    <div class="fm-footer-brand">
                        {brand_lockup(34)}
                        <p>Structured, safety-aware repair guidance for the devices around you.</p>
                        <span class="fm-footer-tag">{icon("lock", 13)} Local history · no account required</span>
                    </div>
                    <div class="fm-footer-col">
                        <span class="fm-footer-label">Capabilities</span>
                        <p>AI diagnosis</p>
                        <p>Vision inspection</p>
                        <p>Repair follow-up</p>
                    </div>
                    <div class="fm-footer-col">
                        <span class="fm-footer-label">Safety boundary</span>
                        <p>Advisory, not a confirmed diagnosis</p>
                        <p>No live-equipment instructions</p>
                        <p>Professional escalation built in</p>
                    </div>
                </div>
                <div class="fm-footer-base">
                    <span>© 2026 FixMate AI</span>
                    <span class="fm-footer-dot"></span>
                    <span>Built with Streamlit &amp; OpenAI</span>
                    <span class="fm-footer-spacer"></span>
                    <span>Diagnostic history stays in this app's local SQLite file.</span>
                </div>
            </footer>
            """)
