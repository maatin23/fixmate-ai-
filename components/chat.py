"""Context-aware repair chat with a custom conversation surface."""

from __future__ import annotations

import streamlit as st

from i18n import t

from ai_service import AIError, chat_reply
from components.cards import render_callout
from components.icons import icon
from components.render import compact_html, html_block
from config import CATEGORY_BY_ID, get_ai_settings
from diagnostic_engine import build_chat_context
from state import begin_diagnosis, go_chat, go_diagnosis, reset_chat
from utils import escape, nl2br

_GENERAL_PROMPTS = [
    "My device won't turn on. What information do you need?",
    "How can I tell if a lithium battery is swollen?",
    "What are safe checks I can do before calling a technician?",
    "How do I prepare a device for professional repair?",
]

_CONTEXT_PROMPTS = [
    "Explain the most likely cause in simple terms.",
    "Which safe checks should I do first, and why?",
    "What should I tell a technician about this fault?",
    "What new evidence would change this diagnosis?",
]


def _queue_prompt(prompt: str) -> None:
    st.session_state.chat_auto_prompt = prompt


def _user_message(content: str) -> str:
    return f"""
    <div class="fm-chat-line fm-chat-line-user">
        <div class="fm-chat-user-bubble">
            <span class="fm-chat-you">You</span>
            <p>{nl2br(content)}</p>
        </div>
        <span class="fm-chat-avatar fm-chat-avatar-you">YOU</span>
    </div>
    """


def _assistant_header() -> str:
    return f"""
    <div class="fm-chat-author">
        <span class="fm-chat-avatar">{icon("sparkles", 16)}</span>
        <div><b>FixMate AI</b><span>repair assistant</span></div>
        <span class="fm-chat-live"><i></i> grounded</span>
    </div>
    """


def _typing_html() -> str:
    return f"""
    <div class="fm-chat-line fm-chat-line-assistant">
        <div class="fm-chat-card fm-chat-typing">
            <div class="fm-chat-author">
                <span class="fm-chat-avatar">{icon("sparkles", 16)}</span>
                <div><b>FixMate AI</b><span>reading your question</span></div>
            </div>
            <div class="fm-typing-dots" aria-label="Assistant is responding"><span></span><span></span><span></span></div>
            <p class="fm-typing-note">Checking the report, safety boundaries and uncertainty.</p>
        </div>
    </div>
    """


def _context_header(diagnostic: dict | None, page_key: str, message_count: int) -> None:
    left, actions = st.columns([5, 1.45], vertical_alignment="center")
    with left:
        if diagnostic:
            inputs = diagnostic.get("input") or {}
            report = diagnostic.get("report") or {}
            session_id = diagnostic.get("id")
            brand = " ".join(filter(None, [inputs.get("manufacturer", ""), inputs.get("model", "")])).strip()
            category_label = inputs.get("category_label") or CATEGORY_BY_ID.get(inputs.get("category", ""), {}).get("label", "Device")
            html_block(
                f"""
                <div class="fm-chat-context">
                    <span class="fm-chat-context-icon">{icon("layers", 18)}</span>
                    <div>
                        <span class="fm-chat-context-kicker">REPORT CONTEXT LOADED</span>
                        <b>{escape(category_label)}{f" · {escape(brand)}" if brand else ""}</b>
                        <p>Session {'#' + str(int(session_id)).zfill(4) if session_id else 'current'} · {escape(str(report.get('severity', '')).title())} severity · the assistant can discuss this report.</p>
                    </div>
                </div>
                """
            )
        else:
            html_block(
                f"""
                <div class="fm-chat-context">
                    <span class="fm-chat-context-icon">{icon("chat", 18)}</span>
                    <div>
                        <span class="fm-chat-context-kicker">GENERAL CONVERSATION</span>
                        <b>No diagnostic report loaded</b>
                        <p>Ask a general repair question. Open or generate a report to bring its evidence into the conversation.</p>
                    </div>
                </div>
                """
            )

    with actions:
        with st.container(key=f"fm-chat-actions-{page_key}"):
            if page_key == "ask":
                st.button(
                    "Open report" if diagnostic else "Start diagnosis",
                    key=f"chat_goto_{page_key}",
                    on_click=go_diagnosis if diagnostic else begin_diagnosis,
                    width="stretch",
                )
            else:
                st.button(t("Ask AI workspace"), key=f"chat_open_{page_key}", on_click=go_chat, width="stretch")
            st.button(
                "Clear conversation",
                key=f"chat_clear_{page_key}",
                on_click=reset_chat,
                disabled=not message_count,
                width="stretch",
            )


def _generate(diagnostic: dict | None, typing_placeholder) -> None:
    typing_placeholder.markdown(compact_html(_typing_html()), unsafe_allow_html=True)
    conversation = list(st.session_state.chat_messages)
    try:
        reply = chat_reply(conversation, build_chat_context(diagnostic))
    except AIError as exc:
        st.session_state.chat_error = exc.message
        typing_placeholder.empty()
        st.rerun()
    except Exception:
        st.session_state.chat_error = (
            "An unexpected error interrupted the reply. No answer was generated. Please retry."
        )
        typing_placeholder.empty()
        st.rerun()

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
    st.session_state.chat_error = None
    typing_placeholder.empty()
    st.rerun()


def render_chat(diagnostic: dict | None, *, page_key: str) -> None:
    settings = get_ai_settings()
    messages = st.session_state.chat_messages
    pending = st.session_state.get("chat_auto_prompt")
    if pending:
        st.session_state.chat_auto_prompt = None
        messages.append({"role": "user", "content": str(pending)})

    _context_header(diagnostic, page_key, len(messages))

    if not settings.configured:
        render_callout(
            "warn",
            "lock",
            "AI key required for chat",
            "Add OPENAI_API_KEY to .env or Streamlit secrets, then restart. FixMate will not invent a simulated reply.",
        )

    if not messages:
        html_block(
            f"""
            <div class="fm-chat-empty">
                <span class="fm-chat-empty-orb">{icon("chat", 28)}</span>
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>{'REPORT DISCUSSION' if diagnostic else 'REPAIR CONVERSATION'}</span>
                <h3>{'Ask about this diagnosis' if diagnostic else 'What is the device doing?'}</h3>
                <p>{'Ask for a simpler explanation, a step-by-step walkthrough, or the questions worth asking a technician. The loaded report is used as context.' if diagnostic else 'Describe the device, the symptom and anything unusual. For a structured report, start a diagnosis instead.'}</p>
            </div>
            """
        )
        prompts = _CONTEXT_PROMPTS if diagnostic else _GENERAL_PROMPTS
        html_block('<div class="fm-prompt-label">Suggested questions</div>')
        for row in range(0, len(prompts), 2):
            cols = st.columns(2, gap="small")
            for offset, (col, prompt) in enumerate(zip(cols, prompts[row : row + 2])):
                with col:
                    st.button(
                        prompt,
                        key=f"chat_prompt_{page_key}_{row}_{offset}",
                        on_click=_queue_prompt,
                        args=(prompt,),
                        disabled=not settings.configured,
                        width="stretch",
                    )

    for index, message in enumerate(messages):
        content = str(message.get("content", ""))
        if message.get("role") == "user":
            html_block(_user_message(content))
        else:
            with st.container(key=f"fm-chat-card-{page_key}-{st.session_state.chat_nonce}-{index}"):
                html_block(_assistant_header())
                st.markdown(content)

    error = st.session_state.get("chat_error")
    if error:
        render_callout(
            "danger",
            "alert",
            "The assistant could not answer",
            escape(error).replace("\n", "<br>"),
            raw_body=True,
        )

    typing_placeholder = st.empty()
    if pending:
        _generate(diagnostic, typing_placeholder)

    with st.container(key=f"fm-chat-composer-{page_key}"):
        with st.form(key=f"chat_form_{page_key}_{st.session_state.chat_nonce}", clear_on_submit=True):
            prompt = st.text_area(
                "Your question",
                key=f"chat_input_{page_key}_{st.session_state.chat_nonce}",
                placeholder=t("Ask a follow-up, request simpler wording, or describe what happened next…"),
                max_chars=1500,
                height=104,
                label_visibility="collapsed",
            )
            send_col, note_col = st.columns([1, 3], vertical_alignment="center")
            with send_col:
                submitted = st.form_submit_button(
                    "Send message",
                    type="primary",
                    disabled=not settings.configured,
                    width="stretch",
                )
            with note_col:
                html_block(
                    f'<p class="fm-composer-note">{icon("shield", 12)} Answers are grounded in the loaded report. Never work on live electrical equipment.</p>'
                )

    if submitted:
        cleaned = " ".join(str(prompt or "").split())
        if len(cleaned) < 2:
            st.warning("Type a question before sending.")
        else:
            st.session_state.chat_messages.append({"role": "user", "content": cleaned[:1500]})
            st.session_state.chat_error = None
            _generate(diagnostic, typing_placeholder)
