"""Local diagnostic dashboard driven exclusively by stored SQLite data."""

from __future__ import annotations

import streamlit as st

from components.cards import (
    empty_state,
    metric_card,
    page_header,
    render_metrics,
)
from components.icons import icon
from components.render import html_block
from config import CATEGORY_BY_ID, DEVICE_CATEGORIES
from database import get_stats
from state import begin_diagnosis, choose_device, go_history, open_saved_diagnostic
from utils import escape, relative_time, severity_tone, truncate


def _chart(stats: dict) -> None:
    activity = stats["activity"]
    counts = [day["count"] for day in activity]
    peak = max(counts) if counts else 0
    week_total = sum(counts)

    if not week_total:
        bars = "".join(
            f'<div class="fm-activity-col"><span class="fm-activity-value">0</span>'
            f'<div class="fm-activity-track"><span class="is-zero"></span></div>'
            f'<small>{escape(day["label"])}</small></div>'
            for day in activity
        )
        empty_note = '<p class="fm-chart-empty">No sessions in the last 7 days. Older sessions remain in history.</p>'
    else:
        bars = ""
        for day in activity:
            count = day["count"]
            height = round((count / peak) * 100) if peak else 0
            css_height = f"{max(5, height)}%" if count else "0%"
            bars += (
                f'<div class="fm-activity-col" title="{count} session{"s" if count != 1 else ""} on {escape(day["date"])}">'
                f'<span class="fm-activity-value">{count}</span>'
                f'<div class="fm-activity-track"><span style="height:{css_height}"></span></div>'
                f"<small>{escape(day['label'])}</small></div>"
            )
        empty_note = ""

    html_block(
        f"""
        <div class="fm-dash-card fm-activity-card">
            <div class="fm-dash-card-head">
                <div><span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>REAL ACTIVITY</span><h3>Sessions this week</h3></div>
                <span class="fm-dash-badge">{week_total} in 7 days</span>
            </div>
            <div class="fm-activity-chart" role="img" aria-label="Diagnostics created per day over the last seven days">{bars}</div>
            {empty_note}
            <div class="fm-chart-legend"><span>Daily intake count</span><span>Stored locally</span></div>
        </div>
        """
    )


def _categories(stats: dict) -> None:
    total = max(1, stats["total"])
    rows = []
    for index, category in enumerate(stats["categories"]):
        count = category["count"]
        pct = round(count / total * 100)
        config = CATEGORY_BY_ID.get(category["id"], {})
        rows.append(
            f"""
            <div class="fm-dist-row">
                <span class="fm-dist-icon fm-dist-tone-{index % 4}">{icon(config.get("icon", "chip"), 15)}</span>
                <div class="fm-dist-body">
                    <div class="fm-dist-top"><b>{escape(category["label"])}</b><span>{count} · {pct}%</span></div>
                    <div class="fm-dist-track"><span style="width:{max(3, pct)}%"></span></div>
                </div>
            </div>
            """
        )
    body = "".join(rows) or '<p class="fm-chart-empty">No categories yet.</p>'
    html_block(
        f"""
        <div class="fm-dash-card fm-dist-card">
            <div class="fm-dash-card-head">
                <div><span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>DEVICE MIX</span><h3>Frequent categories</h3></div>
                <span class="fm-dash-badge">{stats["category_count"]} explored</span>
            </div>
            <div class="fm-dist-list">{body}</div>
            <p class="fm-chart-legend">Share of all {stats["total"]} stored diagnostic{'s' if stats["total"] != 1 else ''}.</p>
        </div>
        """
    )


def _recent(stats: dict) -> None:
    recent = stats["recent"]
    rows = []
    for item in recent:
        category = CATEGORY_BY_ID.get(item["category"], {})
        brand = " ".join(filter(None, [item.get("manufacturer", ""), item.get("model", "")])).strip()
        title = brand or item.get("category_label", "Device")
        tone = severity_tone(item.get("severity", "moderate"))
        rows.append(
            f"""
            <div class="fm-recent-copy">
                <span class="fm-recent-icon">{icon(category.get("icon", "chip"), 18)}</span>
                <div class="fm-recent-main">
                    <div class="fm-recent-top">
                        <b>{escape(title)}</b>
                        <span class="fm-tag fm-tag-{tone}">{escape(str(item.get("severity", "moderate")).title())}</span>
                    </div>
                    <span class="fm-recent-meta">{escape(item.get("category_label", "Device"))} · {escape(relative_time(item.get("created_at")))}</span>
                    <p>{escape(truncate(item.get("summary", ""), 150))}</p>
                </div>
            </div>
            """
        )

    items = []
    for item, copy in zip(recent, rows):
        with st.container(key=f"fm-dash-recent-{item['id']}"):
            left, right = st.columns([5, 1.1], vertical_alignment="center")
            with left:
                html_block(copy)
            with right:
                st.button(
                    "Open",
                    key=f"dash_open_{item['id']}",
                    on_click=open_saved_diagnostic,
                    args=(item["id"],),
                    width="stretch",
                )
    if not recent:
        html_block('<p class="fm-chart-empty">No sessions yet.</p>')


def _quick_start(stats: dict) -> None:
    categories = stats["categories"][:4]
    if not categories:
        categories = [{"id": category["id"], "label": category["label"], "count": 0} for category in DEVICE_CATEGORIES[:4]]

    with st.container(key="fm-quick-card"):
        html_block(
            f"""
            <div class="fm-dash-card-head">
                <div><span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>QUICK START</span><h3>Diagnose again</h3></div>
            </div>
            """
        )
        for row_start in range(0, len(categories), 2):
            cols = st.columns(2, gap="small")
            for col, category in zip(cols, categories[row_start : row_start + 2]):
                config = CATEGORY_BY_ID.get(category["id"], {})
                with col:
                    with st.container(key=f"fm-quick-tile-{category['id']}"):
                        html_block(
                            f"""
                            <div class="fm-quick-tile">
                                <span class="fm-quick-icon">{icon(config.get("icon", "chip"), 18)}</span>
                                <div><b>{escape(category.get("label", config.get("label", "Device")))}</b>
                                <span>{'most used' if category.get("count") else 'start here'}</span></div>
                            </div>
                            """
                        )
                        st.button(
                            "Diagnose",
                            key=f"dash_quick_{category['id']}",
                            on_click=choose_device,
                            args=(category["id"],),
                            width="stretch",
                        )
        st.button("Browse all devices", key="dash_browse", on_click=begin_diagnosis, args=(), width="stretch")


def render() -> None:
    stats = get_stats()
    page_header(
        "DASHBOARD",
        "Your diagnostic history,<br>at a glance.",
        "Every number on this page comes from this app's local SQLite file. There is no demo data, cloud account, or shared usage count.",
    )

    if stats["total"] == 0:
        empty_state(
            "activity",
            "No diagnostics yet.",
            "Generate your first report and this dashboard will fill with real sessions, device categories and a seven-day activity chart.",
            "Start a diagnosis",
            begin_diagnosis,
            key="dashboard",
            args=(),
        )
        html_block(
            f"""
            <div class="fm-dash-empty-grid">
                <div class="fm-dash-empty-card"><span>{icon("gauge", 20)}</span><b>Session metrics</b><p>Totals, referral rate and category coverage appear once a report is stored.</p></div>
                <div class="fm-dash-empty-card"><span>{icon("activity", 20)}</span><b>Activity chart</b><p>A seven-day view built from actual creation timestamps, never estimated.</p></div>
                <div class="fm-dash-empty-card"><span>{icon("history", 20)}</span><b>Recent timeline</b><p>The latest sessions with direct links back into their full reports.</p></div>
            </div>
            """
        )
        return

    percent_pro = round(stats["professional_count"] / stats["total"] * 100)
    render_metrics(
        [
            metric_card("Total diagnostics", str(stats["total"]), "Stored in local SQLite", "history", "cyan"),
            metric_card("Categories explored", f"{stats['category_count']} / 8", "Distinct device types", "grid", "blue"),
            metric_card("Professional referrals", f"{percent_pro}%", f"{stats['professional_count']} of {stats['total']} sessions", "wrench", "violet"),
            metric_card("Last activity", relative_time(stats["last_activity"]), "Most recent saved session", "clock", "steel"),
        ]
    )

    chart_col, cat_col = st.columns([1.45, 1], gap="medium")
    with chart_col:
        _chart(stats)
    with cat_col:
        _categories(stats)

    recent_col, quick_col = st.columns([1.45, 1], gap="medium")
    with recent_col:
        html_block(
            f"""
            <div class="fm-dash-card-head fm-dash-external-head">
                <div><span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>RECENT SESSIONS</span><h3>Pick up where you left off</h3></div>
            </div>
            """
        )
        _recent(stats)
        st.button("Open full history", key="dash_history", on_click=go_history, width="stretch")
    with quick_col:
        _quick_start(stats)
