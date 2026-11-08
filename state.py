"""Session state helpers and navigation callbacks.

All navigation should run through these helpers inside Streamlit button
callbacks, which keeps the custom navbar and the rendered page in sync.
"""

from __future__ import annotations

import streamlit as st

from database import get_diagnostic

PAGE_LABELS = {
    "home": "Home",
    "diagnosis": "Diagnose",
    "dashboard": "Dashboard",
    "history": "History",
    "chat": "Ask AI",
    "about": "About",
}
LABEL_TO_PAGE = {label: page for page, label in PAGE_LABELS.items()}

_DEFAULTS = {
    "theme": "dark",
    "lang": "en",
    "lang_chosen": False,
    "lang_picked": False,
    "view": None,
    "page": "home",
    "nav_choice": "Home",
    "selected_device": None,
    "current_diagnostic": None,
    "chat_messages": [],
    "chat_auto_prompt": None,
    "chat_error": None,
    "chat_nonce": 0,
    "vision_upload_nonce": 0,
    "vision_error": None,
    "vision_pending": False,
    "vision_reopen": False,
    "diagnosis_form_nonce": 0,
    "diagnosis_error": None,
    "confirm_delete_id": None,
    "confirm_clear_history": False,
    "flash": None,
}


def init_state() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.get("page") not in PAGE_LABELS:
        st.session_state.page = "home"
    st.session_state.nav_choice = PAGE_LABELS[st.session_state.page]


def navigate(page: str) -> None:
    if page not in PAGE_LABELS:
        page = "home"
    st.session_state.page = page
    st.session_state.nav_choice = PAGE_LABELS[page]


def set_flash(kind: str, message: str) -> None:
    st.session_state.flash = (kind, message)


def clear_flash() -> None:
    st.session_state.flash = None


def _reset_conversation() -> None:
    st.session_state.chat_messages = []
    st.session_state.chat_auto_prompt = None
    st.session_state.chat_error = None
    st.session_state.chat_nonce += 1
    st.session_state.vision_error = None
    st.session_state.vision_pending = False
    st.session_state.vision_upload_nonce += 1


def begin_diagnosis(category_id: str | None = None) -> None:
    """Start a clean diagnostic session and move to the intake form."""
    st.session_state.current_diagnostic = None
    st.session_state.selected_device = category_id
    st.session_state.diagnosis_form_nonce += 1
    st.session_state.diagnosis_error = None
    st.session_state.vision_reopen = False
    _reset_conversation()
    navigate("diagnosis")


def choose_device(category_id: str) -> None:
    st.session_state.current_diagnostic = None
    st.session_state.selected_device = category_id
    st.session_state.diagnosis_form_nonce += 1
    st.session_state.diagnosis_error = None
    st.session_state.vision_error = None
    st.session_state.vision_reopen = False
    navigate("diagnosis")


def clear_device_selection() -> None:
    st.session_state.selected_device = None
    st.session_state.diagnosis_form_nonce += 1
    st.session_state.diagnosis_error = None


def load_generated_diagnostic(diagnostic: dict) -> None:
    st.session_state.current_diagnostic = diagnostic
    st.session_state.selected_device = diagnostic["input"]["category"]
    st.session_state.diagnosis_error = None
    st.session_state.vision_error = None
    st.session_state.vision_reopen = False
    _reset_conversation()


def open_saved_diagnostic(diagnostic_id: int) -> None:
    diagnostic = get_diagnostic(int(diagnostic_id))
    if not diagnostic:
        set_flash("error", "That saved session could not be found. It may have been deleted.")
        navigate("history")
        return

    st.session_state.current_diagnostic = diagnostic
    st.session_state.selected_device = diagnostic["input"]["category"]
    st.session_state.diagnosis_error = None
    st.session_state.confirm_delete_id = None
    st.session_state.confirm_clear_history = False
    _reset_conversation()
    set_flash("success", "Saved diagnostic opened. Image findings are included if available.")
    navigate("diagnosis")


def delete_saved_diagnostic(diagnostic_id: int) -> None:
    from database import delete_diagnostic

    if delete_diagnostic(int(diagnostic_id)):
        current = st.session_state.get("current_diagnostic")
        if current and current.get("id") == int(diagnostic_id):
            st.session_state.current_diagnostic = None
        set_flash("success", "Diagnostic deleted from local history.")
    else:
        set_flash("error", "The diagnostic could not be deleted. It may already be gone.")
    st.session_state.confirm_delete_id = None


def request_clear_history() -> None:
    from database import clear_diagnostics

    removed = clear_diagnostics()
    st.session_state.confirm_clear_history = False
    if removed:
        set_flash("success", f"Cleared {removed} diagnostic record{'s' if removed != 1 else ''} from local history.")
    else:
        set_flash("info", "History was already empty.")


def reset_chat() -> None:
    _reset_conversation()
    set_flash("info", "Conversation cleared. Your diagnostic context is still loaded.")


def go_home() -> None:
    navigate("home")


def go_diagnosis() -> None:
    navigate("diagnosis")


def go_dashboard() -> None:
    navigate("dashboard")


def go_history() -> None:
    navigate("history")


def go_about() -> None:
    navigate("about")


def go_chat() -> None:
    navigate("chat")
