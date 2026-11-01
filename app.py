import streamlit as st

from config import ASSETS_DIR
from state import init_state
from styles import inject_styles

st.set_page_config(
    page_title="FixMate AI — Diagnosed Smarter",
    page_icon=str(ASSETS_DIR / "favicon.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "FixMate AI — safety-first AI repair triage. Advisory guidance only.",
    },
)

from components.navbar import render_footer, render_navbar  # noqa: E402
from database import init_db  # noqa: E402
from pages import about, chat, dashboard, diagnosis, history, home  # noqa: E402
from state import clear_flash  # noqa: E402

_PAGE_RENDERERS = {
    "home": home.render,
    "diagnosis": diagnosis.render,
    "dashboard": dashboard.render,
    "history": history.render,
    "chat": chat.render,
    "about": about.render,
}


def _render_flash() -> None:
    flash = st.session_state.get("flash")
    if not flash:
        return
    kind, message = flash
    renderer = {
        "success": st.success,
        "error": st.error,
        "warning": st.warning,
        "info": st.info,
    }.get(kind, st.info)
    renderer(message)
    clear_flash()


def main() -> None:
    inject_styles()
    init_state()
    init_db()

    render_navbar()
    _render_flash()

    page = st.session_state.get("page", "home")
    renderer = _PAGE_RENDERERS.get(page, home.render)
    renderer()

    render_footer()


if __name__ == "__main__":
    main()
