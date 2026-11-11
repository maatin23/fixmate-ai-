"""Reusable layout pieces, device cards, empty states and loading UI."""

from __future__ import annotations

import re
from typing import Callable

import streamlit as st

from i18n import t

from components.icons import icon
from components.mascot import mascot
from components.render import compact_html, html_block
from config import DEVICE_CATEGORIES
from utils import escape

_ACCENTS = ["cyan", "blue", "violet", "steel"]


def section_header(eyebrow: str, title: str, copy: str = "", center: bool = False) -> None:
    alignment = " fm-center" if center else ""
    copy_html = f'<p class="fm-section-copy">{copy}</p>' if copy else ""
    html_block(
        f"""
        <div class="fm-section-head{alignment}">
            <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>{escape(eyebrow)}</span>
            <div class="fm-section-title-row">
                <h2>{title}</h2>
                {copy_html}
            </div>
        </div>
        """)


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    html_block(
        f"""
        <header class="fm-page-head">
            <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>{escape(eyebrow)}</span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </header>
        """)


def device_card_header(category: dict, index: int) -> str:
    accent = _ACCENTS[index % len(_ACCENTS)]
    return f"""
        <div class="fm-device-card fm-accent-{accent}">
            <div class="fm-device-card-top">
                <span class="fm-icon-tile">{icon(category["icon"], 26)}</span>
                <span class="fm-device-index">{index + 1:02d}</span>
            </div>
            <div class="fm-device-card-body">
                <h3>{escape(category["label"])}</h3>
                <p>{escape(category["description"])}</p>
            </div>
            <div class="fm-device-card-tag">
                <span class="fm-mini-dot"></span>{escape(category["tagline"])}
            </div>
        </div>
    """


def render_device_grid(
    on_select: Callable[[str], None],
    key_prefix: str,
    categories: list[dict] | None = None,
    button_label: str = "Diagnose",
) -> None:
    categories = categories or DEVICE_CATEGORIES
    for row_start in range(0, len(categories), 4):
        cols = st.columns(4, gap="medium")
        for offset, category in enumerate(categories[row_start : row_start + 4]):
            index = row_start + offset
            with cols[offset]:
                with st.container(key=f"fm-cat-{key_prefix}-{category['id']}"):
                    html_block(device_card_header(category, index))
                    st.button(
                        f"{t(button_label)} →",
                        key=f"{key_prefix}_device_{category['id']}",
                        width="stretch",
                        on_click=on_select,
                        args=(category["id"],),
                    )


def metric_card(label: str, value: str, note: str, icon_name: str, accent: str = "cyan") -> str:
    return f"""
        <div class="fm-metric fm-metric-{accent}">
            <div class="fm-metric-top">
                <span class="fm-metric-label">{escape(label)}</span>
                <span class="fm-metric-icon">{icon(icon_name, 18)}</span>
            </div>
            <span class="fm-metric-value">{escape(value)}</span>
            <span class="fm-metric-note">{escape(note)}</span>
        </div>
    """


def render_metrics(cards: list[str]) -> None:
    html_block(f'<div class="fm-metric-grid">{"".join(cards)}</div>')


def loader_html(title: str = "Checking your device…", subtitle: str = "I'm reading your symptoms, ranking the causes and running the safety checks.") -> str:
    return f"""
        <div class="fm-loader2" role="status" aria-live="polite">
            <div class="fm-loader2-card">
                {mascot("l")}
                <h3>{escape(title)}</h3>
                <p>{escape(subtitle)}</p>
                <ul class="fm-loader2-steps">
                    <li style="--d:0s"><i></i><span>Reading your symptoms</span></li>
                    <li style="--d:2s"><i></i><span>Running safety checks</span></li>
                    <li style="--d:4s"><i></i><span>Writing your plan</span></li>
                </ul>
                <p class="fm-loader2-tip">Tip: unplug the device before you check anything.</p>
            </div>
        </div>
    """


def show_loader(placeholder, title: str, subtitle: str) -> None:
    placeholder.markdown(compact_html(loader_html(title, subtitle)), unsafe_allow_html=True)


def empty_state(
    icon_name: str,
    title: str,
    copy: str,
    action_label: str,
    on_click: Callable,
    *,
    key: str,
    args: tuple = (),
) -> None:
    with st.container(key=f"fm-empty-{key}"):
        html_block(
            f"""
            <div class="fm-empty-state">
                <span class="fm-empty-icon">{icon(icon_name, 26)}</span>
                <h3>{escape(title)}</h3>
                <p>{escape(copy)}</p>
            </div>
            """)
        left, mid, right = st.columns([1.2, 1.1, 1.2])
        with mid:
            st.button(action_label, key=f"empty_action_{key}", type="primary", width="stretch", on_click=on_click, args=args)


def callout(kind: str, icon_name: str, title: str, body: str, *, raw_body: bool = False) -> str:
    body_html = body if raw_body else f"<p>{escape(body)}</p>"
    return f"""
        <div class="fm-callout fm-callout-{escape(kind)}">
            <span class="fm-callout-icon">{icon(icon_name, 18)}</span>
            <div><strong>{escape(title)}</strong>{body_html}</div>
        </div>
    """


def render_callout(kind: str, icon_name: str, title: str, body: str, *, raw_body: bool = False) -> None:
    html_block(callout(kind, icon_name, title, body, raw_body=raw_body))


def setup_card() -> str:
    return f"""
        <div class="fm-setup-card">
            <div class="fm-setup-icon">{icon("lock", 22)}</div>
            <div class="fm-setup-copy">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>AI CONNECTION REQUIRED</span>
                <h3>Connect an OpenAI API key to run live analysis.</h3>
                <p>Add <code>OPENAI_API_KEY</code> to a local <code>.env</code> file, or to the app secrets when deployed.
                Restart the app after changing local environment variables. No mock results are generated when the API
                is unavailable.</p>
                <div class="fm-setup-rows">
                    <span><b>Local</b> OPENAI_API_KEY=sk-… in .env</span>
                    <span><b>Cloud</b> App settings → Secrets → OPENAI_API_KEY</span>
                </div>
            </div>
        </div>
    """


def page_kicker(html_text: str) -> None:
    html_block(f'<div class="fm-kicker-line">{html_text}</div>')


def tag(text: str, tone: str = "neutral") -> str:
    return f'<span class="fm-tag fm-tag-{escape(tone)}">{escape(text)}</span>'


def chips(items: list[str], limit: int = 8) -> str:
    shown = [f'<span class="fm-chip">{escape(item)}</span>' for item in items[:limit] if str(item).strip()]
    if not shown:
        return '<span class="fm-muted-text">None provided</span>'
    return "".join(shown)


def divider(text: str = "") -> None:
    if text:
        html_block(f'<div class="fm-rule"><span>{escape(text)}</span></div>')
    else:
        html_block('<div class="fm-rule"></div>')


def error_message_block(message: str, title: str = "We couldn't complete that AI request.") -> str:
    body = escape(message).replace("\n", "<br>")
    body = re.sub(r"`([^`]+)`", r"<code>\1</code>", body)
    return f"""
        <div class="fm-error-card">
            <span class="fm-error-icon">{icon("alert", 20)}</span>
            <div>
                <strong>{escape(title)}</strong>
                <p>{body}</p>
            </div>
        </div>
    """
