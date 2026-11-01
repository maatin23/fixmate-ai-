"""Searchable, local-only diagnostic history."""

from __future__ import annotations

import streamlit as st

from components.cards import empty_state, page_header
from components.icons import icon
from components.render import html_block
from config import CATEGORY_BY_ID, DEVICE_CATEGORIES
from database import get_stats, list_diagnostics
from state import (
    begin_diagnosis,
    delete_saved_diagnostic,
    open_saved_diagnostic,
    request_clear_history,
)
from utils import escape, format_timestamp, relative_time, severity_tone, truncate

_ALL_CATEGORIES = "All devices"
_CATEGORY_LABELS = {category["label"]: category["id"] for category in DEVICE_CATEGORIES}


def _ask_delete(diagnostic_id: int) -> None:
    st.session_state.confirm_delete_id = int(diagnostic_id)


def _cancel_delete() -> None:
    st.session_state.confirm_delete_id = None


def _ask_clear() -> None:
    st.session_state.confirm_clear_history = True


def _cancel_clear() -> None:
    st.session_state.confirm_clear_history = False


def _clear_filters() -> None:
    st.session_state["hist_search"] = ""
    st.session_state["hist_category"] = _ALL_CATEGORIES


def _confirmation(diagnostic_id: int) -> None:
    html_block(
        f"""
        <div class="fm-delete-confirm">
            <span class="fm-delete-icon">{icon("trash", 20)}</span>
            <div>
                <b>Delete diagnostic #{int(diagnostic_id):04d}?</b>
                <p>This removes the report, intake details and any stored image findings from this device's SQLite history. It cannot be undone.</p>
            </div>
        </div>
        """
    )
    confirm_col, cancel_col, _ = st.columns([1, 1, 3])
    with confirm_col:
        st.button(
            "Delete permanently",
            key=f"confirm_delete_{diagnostic_id}",
            on_click=delete_saved_diagnostic,
            args=(diagnostic_id,),
            width="stretch",
        )
    with cancel_col:
        st.button("Keep record", key=f"cancel_delete_{diagnostic_id}", on_click=_cancel_delete, width="stretch")


def _card(item: dict) -> None:
    category = CATEGORY_BY_ID.get(item["category"], {})
    brand = " ".join(filter(None, [item.get("manufacturer", ""), item.get("model", "")])).strip()
    title = brand or item.get("category_label", "Device")
    tone = severity_tone(item.get("severity", "moderate"))
    tags = [f'<span class="fm-tag fm-tag-{tone}">{escape(str(item.get("severity", "moderate")).title())}</span>']
    if item.get("professional_recommended"):
        tags.append('<span class="fm-tag fm-tag-high">Pro referral</span>')
    if item.get("has_image_analysis"):
        tags.append('<span class="fm-tag fm-tag-neutral">Visual pass</span>')
    if item.get("hazards"):
        tags.append(f'<span class="fm-tag fm-tag-critical">{len(item["hazards"])} safety flag{"s" if len(item["hazards"]) != 1 else ""}</span>')
    symptoms = " · ".join(item.get("symptoms") or [])[:90]
    meta_line = " · ".join(filter(None, [item.get("category_label", "Device"), symptoms]))

    with st.container(key=f"fm-histrec-{item['id']}"):
        left, actions = st.columns([5.3, 1.15], vertical_alignment="center")
        with left:
            html_block(
                f"""
                <div class="fm-history-copy">
                    <span class="fm-history-icon">{icon(category.get("icon", "chip"), 20)}</span>
                    <div class="fm-history-main">
                        <div class="fm-history-top">
                            <span class="fm-history-date">{escape(relative_time(item.get("created_at")))} · #{int(item["id"]):04d}</span>
                            <div class="fm-history-tags">{''.join(tags)}</div>
                        </div>
                        <h3>{escape(title)}</h3>
                        <p class="fm-history-summary">{escape(truncate(item.get("summary", ""), 210))}</p>
                        <div class="fm-history-meta"><span>{escape(meta_line or "No symptoms listed")}</span><span>{escape(format_timestamp(item.get("created_at")))}</span></div>
                    </div>
                </div>
                """
            )
        with actions:
            st.button(
                "Open report",
                key=f"history_open_{item['id']}",
                on_click=open_saved_diagnostic,
                args=(item["id"],),
                width="stretch",
            )
            st.button(
                "Delete",
                key=f"history_delete_{item['id']}",
                on_click=_ask_delete,
                args=(item["id"],),
                width="stretch",
            )


def _danger_zone(total: int) -> None:
    with st.expander("Storage & destructive actions", expanded=False):
        html_block(
            f"""
            <div class="fm-storage-note">
                <span>{icon("database", 18)}</span>
                <div><b>Local-only storage</b>
                <p>History lives in a SQLite file on the machine running FixMate. There is no account or cloud sync.
                On Streamlit Community Cloud, the filesystem can reset when the app restarts or redeploys, so local history there is best treated as temporary.</p></div>
            </div>
            """
        )
        if not st.session_state.confirm_clear_history:
            st.button(
                f"Clear all {total} stored diagnostic{'s' if total != 1 else ''}",
                key="history_clear_all",
                on_click=_ask_clear,
            )
        else:
            html_block(
                f"""
                <div class="fm-delete-confirm">
                    <span class="fm-delete-icon">{icon("alert", 20)}</span>
                    <div>
                        <b>Clear every stored diagnostic?</b>
                        <p>All {total} records and their image findings will be permanently removed from the local database. This cannot be undone.</p>
                    </div>
                </div>
                """
            )
            confirm_col, cancel_col, _ = st.columns([1, 1, 3])
            with confirm_col:
                st.button(
                    "Yes, clear history",
                    key="history_clear_confirm",
                    on_click=request_clear_history,
                    width="stretch",
                )
            with cancel_col:
                st.button("Cancel", key="history_clear_cancel", on_click=_cancel_clear, width="stretch")


def render() -> None:
    stats = get_stats()
    page_header(
        "HISTORY",
        "Evidence you can<br>come back to.",
        "Search, reopen or remove diagnostic records stored by this app. History is local to this deployment — not a multi-user cloud log.",
    )
    html_block(
        f"""
        <div class="fm-local-banner">
            <span class="fm-local-banner-icon">{icon("database", 20)}</span>
            <div><b>Stored on this machine only</b>
            <p>{stats["total"]} diagnostic{'s' if stats["total"] != 1 else ""} in the local SQLite file. No cloud sync, no account, no data shared with other visitors to a hosted deployment.</p></div>
            <span class="fm-local-chip">{icon("lock", 12)} LOCAL</span>
        </div>
        """
    )

    if stats["total"] == 0:
        empty_state(
            "history",
            "No saved diagnostics yet.",
            "Once a report is generated it lands here automatically — searchable by description, model, summary and error code.",
            "Generate the first report",
            begin_diagnosis,
            key="history",
            args=(),
        )
        return

    with st.container(key="fm-history-filters"):
        search_col, category_col, clear_col = st.columns([2.2, 1.25, 0.8], vertical_alignment="bottom")
        with search_col:
            search = st.text_input(
                "Search history",
                key="hist_search",
                placeholder="Search descriptions, models, summaries or error codes…",
                label_visibility="collapsed",
            )
        with category_col:
            selected_label = st.selectbox(
                "Device category",
                [_ALL_CATEGORIES, *[category["label"] for category in DEVICE_CATEGORIES]],
                key="hist_category",
                label_visibility="collapsed",
            )
        with clear_col:
            st.button("Clear filters", key="history_clear_filters", on_click=_clear_filters, width="stretch")

    category_filter = "" if selected_label == _ALL_CATEGORIES else _CATEGORY_LABELS.get(selected_label, "")
    items = list_diagnostics(search=search, category=category_filter, limit=100)
    filter_note = "all records" if not search and not category_filter else "matching this filter"
    html_block(
        f'<div class="fm-history-count"><span>Showing <b>{len(items)}</b> of <b>{stats["total"]}</b> {escape(filter_note)}</span>'
        f'<span>Newest first · local database</span></div>'
    )

    if st.session_state.confirm_delete_id is not None:
        _confirmation(int(st.session_state.confirm_delete_id))

    if not items:
        html_block(
            f"""
            <div class="fm-empty-state fm-empty-compact">
                <span class="fm-empty-icon">{icon("search", 26)}</span>
                <h3>No records match this search.</h3>
                <p>Try a different term, choose another category, or clear the filters. Deleted records cannot be recovered.</p>
            </div>
            """
        )
        mid_col, _ = st.columns([1, 2])
        with mid_col:
            st.button("Reset filters & show all", key="history_reset_empty", on_click=_clear_filters, width="stretch")
    else:
        for item in items:
            _card(item)

    st.divider()
    _danger_zone(stats["total"])
