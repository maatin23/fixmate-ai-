"""Rendering for diagnostic reports and visual inspection findings."""

from __future__ import annotations

from typing import Any

from components.icons import icon
from urllib.parse import quote_plus

import streamlit as st

from components.render import html_block
from i18n import t
from utils import escape, format_timestamp, severity_tone, title_case

_CONFIDENCE_PCT = {"high": 82, "medium": 56, "low": 30}
_LIKELIHOOD_TONE = {"high": "strong", "medium": "medium", "low": "weak"}


def _tag(label: str, tone: str = "neutral") -> str:
    return f'<span class="fm-tag fm-tag-{escape(tone)}">{escape(label)}</span>'


def _bullets(items: list[str], icon_name: str = "check") -> str:
    if not items:
        return ""
    rows = "".join(
        f'<li><span class="fm-list-icon">{icon(icon_name, 14)}</span><span>{escape(item)}</span></li>'
        for item in items
    )
    return f'<ul class="fm-check-list">{rows}</ul>'


def _section(key: str, title: str, hint: str, body: str, icon_name: str) -> str:
    return f"""
    <section class="fm-report-block fm-block-{escape(key)}">
        <div class="fm-block-head">
            <span class="fm-block-icon">{icon(icon_name, 18)}</span>
            <h3>{escape(title)}</h3>
            <span class="fm-block-hint">{escape(hint)}</span>
        </div>
        {body}
    </section>
    """


def _hazard_panel(diagnostic: dict) -> str:
    hazards = diagnostic.get("hazards") or []
    notices = diagnostic.get("safety_notices") or []
    if not hazards:
        if not notices:
            return ""
        notice_items = "".join(f"<li>{escape(notice)}</li>" for notice in notices)
        return f"""
        <div class="fm-hazard-panel fm-hazard-caution">
            <div class="fm-hazard-head">
                <span class="fm-hazard-shield">{icon("shield", 22)}</span>
                <div><span class="fm-hazard-kicker">SAFETY LAYER</span><h3>Guardrail notices</h3></div>
            </div>
            <ul class="fm-hazard-notes">{notice_items}</ul>
        </div>
        """

    cards = []
    level_rank = 0
    for hazard in hazards:
        level = str(hazard.get("level", "caution")).lower()
        level_rank = max(level_rank, {"critical": 3, "high": 2, "caution": 1}.get(level, 1))
        cards.append(
            f"""
            <article class="fm-hazard-card fm-hazard-{escape(level)}">
                <div class="fm-hazard-card-top">
                    <span class="fm-hazard-title">{escape(hazard.get("title", "Hazard"))}</span>
                    {_tag(level.title(), level)}
                </div>
                <p>{escape(hazard.get("message", ""))}</p>
                <div class="fm-hazard-action">
                    <span>{icon("bolt", 14)}</span>
                    <p>{escape(hazard.get("action", ""))}</p>
                </div>
            </article>
            """
        )

    hazard_actions = {str(hazard.get("action", "")).strip() for hazard in hazards}
    extra_notices = [
        notice
        for notice in notices
        if str(notice).strip() and str(notice).strip() not in hazard_actions
    ]
    extra_html = ""
    if extra_notices:
        items = "".join(f"<li>{escape(notice)}</li>" for notice in extra_notices)
        extra_html = f'<ul class="fm-hazard-notes">{items}</ul>'

    tone = "critical" if level_rank == 3 else "high" if level_rank == 2 else "caution"
    title = "Stop and read before touching the device" if tone in {"critical", "high"} else "Safety notes for this device"
    return f"""
    <div class="fm-hazard-panel fm-hazard-{tone}">
        <div class="fm-hazard-head">
            <span class="fm-hazard-shield">{icon("alert", 22)}</span>
            <div><span class="fm-hazard-kicker">SAFETY LAYER · {len(hazards)} SIGNAL{'S' if len(hazards) != 1 else ''}</span><h3>{escape(title)}</h3></div>
        </div>
        <div class="fm-hazard-grid">{''.join(cards)}</div>
        {extra_html}
    </div>
    """


def _causes(report: dict) -> str:
    causes = report.get("causes") or []
    if not causes:
        return ""
    cards = []
    for index, cause in enumerate(causes):
        likelihood = str(cause.get("likelihood", "low")).lower()
        quick_test = cause.get("quick_test", "")
        test_html = (
            f'<div class="fm-quick-test"><span class="fm-quick-test-label">{icon("target", 13)} Safe distinguishing test</span>'
            f"<p>{escape(quick_test)}</p></div>"
            if quick_test
            else ""
        )
        cards.append(
            f"""
            <article class="fm-cause-card">
                <span class="fm-cause-rank">{index + 1:02d}</span>
                <div class="fm-cause-main">
                    <div class="fm-cause-top">
                        <h4>{escape(cause.get("title", "Possible cause"))}</h4>
                        {_tag(f"{likelihood.title()} plausibility", _LIKELIHOOD_TONE.get(likelihood, "weak"))}
                    </div>
                    <p>{escape(cause.get("explanation", ""))}</p>
                    {test_html}
                </div>
            </article>
            """
        )
    body = f'<div class="fm-cause-list">{"".join(cards)}</div>'
    return _section(
        "causes",
        "Ranked possible causes",
        "Hypotheses, not confirmed faults",
        body,
        "layers",
    )


def _steps(steps: list[dict], *, advanced: bool = False) -> str:
    if not steps:
        return ""
    rows = []
    for index, step in enumerate(steps):
        expected = step.get("expected_result", "")
        risk = step.get("risk_note", "")
        expected_html = (
            f'<div class="fm-step-expect"><span>{icon("eye", 13)} What to look for</span><p>{escape(expected)}</p></div>'
            if expected
            else ""
        )
        risk_html = (
            f'<div class="fm-step-risk">{icon("alert", 13)} {escape(risk)}</div>' if risk else ""
        )
        rows.append(
            f"""
            <li class="fm-repair-step">
                <span class="fm-step-index">{index + 1:02d}</span>
                <div class="fm-step-main">
                    <h4>{escape(step.get("title", "Step"))}</h4>
                    <p>{escape(step.get("detail", ""))}</p>
                    {expected_html}
                    {risk_html}
                </div>
            </li>
            """
        )
    return f'<ol class="fm-repair-steps">{"".join(rows)}</ol>'


def _professional(report: dict) -> str:
    professional = report.get("professional_repair") or {}
    recommended = bool(professional.get("recommended"))
    urgency = str(professional.get("urgency", "routine")).lower()
    reason = professional.get("reason", "")

    if recommended:
        tone = "urgent" if urgency == "urgent" else "soon"
        status = "Professional repair recommended"
        urgency_label = {"urgent": "Urgent", "soon": "Soon", "routine": "Routine"}.get(urgency, title_case(urgency))
        return f"""
        <div class="fm-pro-panel fm-pro-{tone}">
            <div class="fm-pro-top">
                <span class="fm-pro-icon">{icon("wrench", 22)}</span>
                <div>
                    <span class="fm-pro-kicker">PROFESSIONAL SERVICE · {escape(urgency_label.upper())}</span>
                    <h3>{escape(status)}</h3>
                </div>
                {_tag(urgency_label, "high" if urgency != "urgent" else "critical")}
            </div>
            <p>{escape(reason or "This repair involves work that should be handled by a qualified technician.")}</p>
            <div class="fm-pro-note">{icon("info", 14)} Ask the technician to diagnose before authorising parts or labour. You can share this report as background.</div>
        </div>
        """

    return f"""
    <div class="fm-pro-panel fm-pro-not-required">
        <div class="fm-pro-top">
            <span class="fm-pro-icon">{icon("check", 22)}</span>
            <div>
                <span class="fm-pro-kicker">PROFESSIONAL SERVICE</span>
                <h3>Not flagged as mandatory</h3>
            </div>
            {_tag("No referral flag", "low")}
        </div>
        <p>{escape(reason or "The model did not flag a mandatory professional repair for the evidence provided. Stop and seek a technician if symptoms worsen or you reach a step outside your comfort and skill level.")}</p>
    </div>
    """


def _tools(report: dict) -> str:
    tools = report.get("tools") or []
    if not tools:
        return ""
    rows = []
    for tool in tools:
        scope = str(tool.get("needed_for", "as required")).lower()
        tone = "advanced" if scope == "advanced repair" else "safe" if scope == "safe checks" else "neutral"
        purpose = tool.get("purpose", "")
        rows.append(
            f"""
            <div class="fm-tool">
                <span class="fm-tool-icon">{icon("wrench", 15)}</span>
                <div><b>{escape(tool.get("name", "Tool"))}</b>{f"<p>{escape(purpose)}</p>" if purpose else ""}</div>
                {_tag(scope.title(), tone)}
            </div>
            """
        )
    return _section(
        "tools",
        "Tools & materials",
        "Match the tool to the task, not the other way around",
        f'<div class="fm-tools">{"".join(rows)}</div>',
        "wrench",
    )


def _prevention(report: dict) -> str:
    items = report.get("prevention") or []
    if not items:
        return ""
    return _section(
        "prevention",
        "Reduce repeat risk",
        "General care suggestions",
        _bullets(items, "shield"),
        "shield",
    )


_REPAIR_SEARCH_TERMS = {
    "smartphone": "phone repair",
    "laptop": "laptop repair",
    "desktop": "computer repair",
    "washing_machine": "washing machine repair",
    "refrigerator": "refrigerator repair",
    "air_conditioner": "air conditioner repair",
    "television": "TV repair",
    "tablet": "tablet repair",
    "printer": "printer repair",
    "game_console": "game console repair",
    "router": "router repair",
    "microwave": "microwave repair",
    "dishwasher": "dishwasher repair",
    "smartwatch": "smartwatch repair",
    "headphones": "headphone repair",
}


def _repair_shop_url(inputs: dict) -> str:
    term = _REPAIR_SEARCH_TERMS.get(inputs.get("category", ""), "electronics repair")
    brand = str(inputs.get("manufacturer") or "").strip()
    if brand.lower().startswith("custom") or len(brand) > 30:
        brand = ""
    query = f"{brand} {term} near me".strip()
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(query)


def _repair_shop_button(report: dict, inputs: dict) -> None:
    """Link to a Google Maps search for repair shops. Nothing is stored or sent from the app."""
    with st.container(key="fm-repair-shop"):
        if (report.get("professional_repair") or {}).get("recommended"):
            st.markdown(f"**{t('A professional repair is recommended for this problem.')}**")
        st.link_button(
            t("Find a repair shop near me"),
            _repair_shop_url(inputs),
            icon=":material/location_on:",
            width="stretch",
        )
        st.caption(t("Opens Google Maps in a new tab. Always check reviews and ask for a price before you hand over your device."))


def render_report(diagnostic: dict) -> None:
    report = diagnostic.get("report") or {}
    inputs = diagnostic.get("input") or {}
    severity = str(report.get("severity", "moderate")).lower()
    tone = severity_tone(severity)
    confidence = str(report.get("confidence", "low")).lower()
    confidence_pct = _CONFIDENCE_PCT.get(confidence, 30)
    professional = report.get("professional_repair") or {}

    status_tags = [
        _tag(f"{severity.title()} severity", tone),
        _tag(f"{confidence.title()} confidence", "strong" if confidence == "high" else "weak" if confidence == "low" else "medium"),
    ]
    if professional.get("recommended"):
        status_tags.append(_tag("Professional referral", "high"))

    device = " · ".join(
        filter(
            None,
            [
                inputs.get("category_label", ""),
                " ".join(filter(None, [inputs.get("manufacturer", ""), inputs.get("model", "")])).strip(),
            ],
        )
    )
    session_id = diagnostic.get("id")
    session_label = f"SESSION #{int(session_id):04d}" if session_id else "CURRENT SESSION"
    created = format_timestamp(diagnostic.get("created_at"))

    header = f"""
    <div class="fm-report-hero fm-tone-{tone}">
        <div class="fm-report-hero-top">
            <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>AI DIAGNOSTIC REPORT</span>
            <span class="fm-report-id">{session_label} · {escape(created)}</span>
        </div>
        <div class="fm-report-tags">{''.join(status_tags)}</div>
        <p class="fm-report-summary">{escape(report.get("summary", ""))}</p>
        <div class="fm-report-meta">
            <div><span>DEVICE</span><b>{escape(device or "Not specified")}</b></div>
            <div><span>DIFFICULTY</span><b>{escape(report.get("difficulty", "Not specified"))}</b></div>
            <div><span>EST. REPAIR TIME</span><b>{escape(report.get("estimated_time", "Not specified"))}</b></div>
            <div><span>CONFIDENCE</span><b>{escape(confidence.title())}</b></div>
        </div>
        <div class="fm-confidence">
            <div class="fm-confidence-head"><span>Model confidence in this assessment</span><b>{confidence_pct}%</b></div>
            <div class="fm-confidence-bar"><span style="width:{confidence_pct}%"></span></div>
            <p>Confidence reflects the strength of the description only — not a physical test result.</p>
        </div>
    </div>
    """

    safe_checks = _section(
        "safe-checks",
        "Safe checks you can do",
        "With the device unplugged and powered off",
        _steps(report.get("safe_checks") or [])
        or '<p class="fm-block-empty">No specific basic checks were returned for this case. Do not improvise internal work.</p>',
        "check",
    )

    advanced_steps = report.get("advanced_steps") or []
    if diagnostic.get("advanced_withheld"):
        advanced_body = f"""
        <div class="fm-advanced-lock">
            <span class="fm-lock-icon">{icon("lock", 22)}</span>
            <div>
                <h4>Advanced steps withheld by the safety layer</h4>
                <p>This session contains a hazard pattern where internal repair guidance could be unsafe.
                The safety layer removed advanced steps regardless of what the model suggested.
                Have the device assessed by a qualified technician.</p>
            </div>
        </div>
        """
    elif advanced_steps:
        advanced_body = (
            '<div class="fm-advanced-warning">'
            f"{icon('alert', 15)} Advanced repairs can expose you to hazardous voltage, heat, refrigerant, or moving parts. "
            "Only continue if you have the right skills and tools. When in doubt, stop and call a technician."
            "</div>"
            + _steps(advanced_steps, advanced=True)
        )
    else:
        advanced_body = ""
    advanced = _section(
        "advanced",
        "Advanced repair path",
        "For qualified technicians or experienced hobbyists",
        advanced_body
        or '<p class="fm-block-empty">No advanced steps were returned. Keep to the safe checks above.</p>',
        "wrench",
    )

    uncertainty = _section(
        "uncertainty",
        "What remains uncertain",
        "Read this before acting",
        f'<div class="fm-uncertainty"><span>{icon("gauge", 20)}</span><p>{escape(report.get("uncertainty", ""))}</p></div>',
        "gauge",
    )

    stop_items = report.get("when_to_stop") or []
    stop = _section(
        "stop",
        "When to stop",
        "Hard limits, not suggestions",
        _bullets(stop_items, "alert")
        or '<p class="fm-block-empty">Stop if anything feels unsafe.</p>',
        "alert",
    )

    html_block(
        '<div class="fm-report">'
        + header
        + _hazard_panel(diagnostic)
        + _causes(report)
        + safe_checks
        + advanced
        + _professional(report)
        + _tools(report)
        + uncertainty
        + stop
        + _prevention(report)
        + f'<div class="fm-report-disclaimer">{icon("info", 14)} <span>This report is AI-generated advisory guidance based only on the details and images you supplied. It is not a confirmed diagnosis and does not replace an in-person inspection.</span></div>'
        + "</div>"
    )
    _repair_shop_button(report, inputs)


def _severity_tag(value: str) -> str:
    tone = severity_tone(value)
    return _tag(str(value or "Unclear").title(), tone if tone != "neutral" else "neutral")


def render_image_analysis(analysis: dict | None) -> None:
    if not analysis:
        return

    quality = analysis.get("image_quality") or {}
    severity = analysis.get("overall_severity", "unknown")
    findings = analysis.get("visible_findings") or []
    meta = analysis.get("_meta") or {}

    finding_rows = []
    for finding in findings:
        finding_rows.append(
            f"""
            <div class="fm-finding">
                <div class="fm-finding-main">
                    <span class="fm-finding-area">{escape(finding.get("area", "Unspecified area"))}</span>
                    <p>{escape(finding.get("observation", ""))}</p>
                </div>
                <div class="fm-finding-tags">
                    {_severity_tag(finding.get("severity", "unclear"))}
                    {_tag(f"{str(finding.get('confidence', 'low')).title()} confidence", {"high": "strong", "medium": "medium"}.get(str(finding.get('confidence', 'low')), "weak"))}
                </div>
            </div>
            """
        )

    what_not = analysis.get("what_image_cannot_tell") or []
    next_checks = analysis.get("next_safe_checks") or []
    check_rows = "".join(
        f'<div class="fm-safe-next"><h4>{escape(check.get("title", "Next check"))}</h4><p>{escape(check.get("detail", ""))}</p></div>'
        for check in next_checks
    )
    review = analysis.get("professional_review") or {}
    review_html = ""
    if review.get("recommended"):
        urgency = str(review.get("urgency", "soon")).lower()
        review_html = f"""
        <div class="fm-pro-panel fm-pro-{'urgent' if urgency == 'urgent' else 'soon'} fm-vision-pro">
            <div class="fm-pro-top">
                <span class="fm-pro-icon">{icon("wrench", 22)}</span>
                <div><span class="fm-pro-kicker">VISUAL REVIEW · {escape(urgency.upper())}</span><h3>Professional inspection recommended</h3></div>
                {_tag(urgency.title(), "high" if urgency != "urgent" else "critical")}
            </div>
            <p>{escape(review.get("reason", "Visible evidence warrants an in-person assessment."))}</p>
        </div>
        """

    quality_html = ""
    if not quality.get("usable", True) or quality.get("notes"):
        quality_html = (
            f'<div class="fm-vision-quality">{icon("info", 14)} '
            f"{escape(quality.get('notes') or 'The image may not be clear enough for reliable inspection.')}</div>"
        )

    analyzed_at = format_timestamp(meta.get("analyzed_at")) if meta.get("analyzed_at") else ""
    model_name = meta.get("model", "")

    html_block(
        f"""
        <div class="fm-vision-report">
            <div class="fm-vision-head">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>VISUAL INSPECTION</span>
                <div class="fm-vision-tags">{_severity_tag(severity)}{_tag(f"{len(findings)} visible finding{'s' if len(findings) != 1 else ''}", "neutral")}</div>
            </div>
            <p class="fm-vision-summary">{escape(analysis.get("summary", ""))}</p>
            {quality_html}
            <div class="fm-findings">{''.join(finding_rows) or '<p class="fm-block-empty">No specific visible findings were identified.</p>'}</div>
            <div class="fm-vision-split">
                <div class="fm-vision-col">
                    <h4>{icon("eye", 16)} What the photo cannot tell</h4>
                    {_bullets(what_not, "alert")}
                </div>
                <div class="fm-vision-col">
                    <h4>{icon("check", 16)} Safe next checks</h4>
                    {check_rows or '<p class="fm-block-empty">No camera-based checks were suggested.</p>'}
                </div>
            </div>
            {f'<div class="fm-vision-safety">{icon("shield", 15)} {escape(analysis.get("safety_note", ""))}</div>' if analysis.get("safety_note") else ""}
            {review_html}
            <div class="fm-vision-meta">
                {f"<span>{escape(model_name)}</span>" if model_name else ""}
                {f"<span>{escape(analyzed_at)}</span>" if analyzed_at else ""}
                <span>Visible evidence only</span>
            </div>
            <div class="fm-report-disclaimer">{icon("info", 14)} <span>Image findings describe visible condition only. A photograph cannot confirm internal damage, live electrical state, or the cause of a fault.</span></div>
        </div>
        """
    )
