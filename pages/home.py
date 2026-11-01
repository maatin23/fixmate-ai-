"""Landing page."""

from __future__ import annotations

import streamlit as st

from components.cards import render_device_grid
from components.render import html_block
from components.icons import icon, logo_mark
from state import begin_diagnosis


def _hero() -> None:
    left, right = st.columns([1.05, 0.95], gap="large", vertical_alignment="center")
    with left:
        html_block(
            f"""
            <div class="fm-hero">
                <div class="fm-eyebrow fm-eyebrow-hero">
                    <span class="fm-live-dot"></span> Safety-first repair help
                </div>
                <h1>Describe the problem.<br><span class="fm-grad-text">Get a safe plan.</span></h1>
                <p class="fm-hero-sub">
                    Describe the fault or attach a photo. FixMate maps plausible causes, separates safe checks
                    from advanced repairs, and shows its uncertainty before you pick up a tool.
                </p>
                <div class="fm-hero-assurance">
                    <span>{icon("shield", 14)} Safety guardrails</span>
                    <span>{icon("eye", 14)} Vision inspection</span>
                    <span>{icon("database", 14)} Local history</span>
                </div>
            </div>
            """)
        cta_a, cta_b = st.columns([1, 1], gap="small")
        with cta_a:
            st.button(
                "Start diagnosis",
                key="hero_start",
                type="primary",
                width="stretch",
                on_click=begin_diagnosis,
                args=(),
            )
        with cta_b:
            html_block(
                """
                <a class="fm-btn fm-btn-ghost fm-btn-inline" href="#device-lab">
                    Explore devices <span class="fm-btn-arrow">↓</span>
                </a>
                """)
        html_block(
            '<p class="fm-hero-footnote">AI-assisted guidance, not a confirmed diagnosis. No account required.</p>')

    with right:
        html_block(
            """
            <div class="bp-stage" aria-label="Blueprint drawing of a phone with the faulty charging port circled">
            <svg class="bp" viewBox="0 0 420 470" xmlns="http://www.w3.org/2000/svg">
                <g class="ln">
                    <path class="dr" pathLength="1" style="--i:0" d="M120 30h170M120 22v16M290 22v16"/>
                    <rect class="dr" pathLength="1" style="--i:1" x="120" y="52" width="170" height="340" rx="26"/>
                    <rect class="dr" pathLength="1" style="--i:2" x="135" y="76" width="140" height="292" rx="10"/>
                    <path class="dr" pathLength="1" style="--i:3" d="M185 64h40"/>
                    <path class="dr" pathLength="1" style="--i:4" d="M240 92l-22 46 18 14-26 52"/>
                    <rect class="dr" pathLength="1" style="--i:5" x="165" y="250" width="76" height="38" rx="6"/>
                    <path class="dr" pathLength="1" style="--i:5" d="M241 262h8v14h-8"/>
                    <circle class="gear" cx="350" cy="130" r="30" stroke-width="9" stroke-dasharray="7 7"/>
                    <circle cx="350" cy="130" r="19"/>
                </g>
                <text class="big" x="178" y="276">12%</text>
                <text x="120" y="14">6.1 in</text>
                <g class="late">
                    <circle class="ring" cx="205" cy="392" r="13"/>
                    <circle class="of" cx="205" cy="392" r="5"/>
                    <path class="ln or" d="M205 398v28h195"/>
                    <text x="214" y="420">A  charging port 78%</text>
                    <text x="214" y="446" style="fill:#b4c2ff">fig. 1 - most likely cause</text>
                </g>
            </svg>
            </div>
            """)


def _ticker() -> None:
    items = [
        "8 device categories",
        "Vision-assisted inspection",
        "Ranked hypotheses",
        "Safety-first guardrails",
        "Local SQLite history",
        "Confidence-aware reports",
        "Contextual repair chat",
    ]
    content = "".join(f'<span>{item}</span><i></i>' for item in items)
    html_block(
        f'<div class="fm-ticker"><div class="fm-ticker-track">{content}{content}</div></div>')


def _devices() -> None:
    html_block('<div id="device-lab" class="fm-anchor"></div>')
    html_block(
        """
        <div class="fm-section-head">
            <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>DEVICE LAB</span>
            <div class="fm-section-title-row">
                <h2>Choose your device.<br>We'll map the fault.</h2>
                <p class="fm-section-copy">Each intake adapts to the hardware — from battery behaviour and screen
                condition to drainage, cooling, error codes and unusual signs.</p>
            </div>
        </div>
        """)
    render_device_grid(begin_diagnosis, "home")
    html_block(
        '<p class="fm-center-note">Works with smartphones, computers, large appliances, displays and other electronics.</p>')


def _how_it_works() -> None:
    steps = [
        {
            "num": "01",
            "icon": "tune",
            "title": "Describe the fault",
            "copy": "A guided intake captures the symptoms, onset, error codes and any unusual sights or smells. Add photos if you have them.",
            "tag": "2–3 minute intake",
        },
        {
            "num": "02",
            "icon": "layers",
            "title": "Read the evidence",
            "copy": "The AI ranks plausible causes, explains its reasoning and surfaces the uncertainty instead of hiding it.",
            "tag": "Structured report",
        },
        {
            "num": "03",
            "icon": "chat",
            "title": "Check, then act",
            "copy": "Start with de-energized checks, inspect visible damage with vision, and ask follow-ups before deciding on a repair.",
            "tag": "Context-aware follow-up",
        },
    ]
    cards = "".join(
        f"""
        <article class="fm-step-card">
            <div class="fm-step-top">
                <span class="fm-step-number">{step['num']}</span>
                <span class="fm-icon-tile fm-step-icon">{icon(step['icon'], 22)}</span>
            </div>
            <h3>{step['title']}</h3>
            <p>{step['copy']}</p>
            <span class="fm-step-tag">{step['tag']}</span>
        </article>
        """
        for step in steps
    )
    html_block(
        f"""
        <section class="fm-how">
            <div class="fm-section-head">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>HOW IT WORKS</span>
                <div class="fm-section-title-row">
                    <h2>From symptom to a safer next step.</h2>
                    <p class="fm-section-copy">No black box. Each stage shows what went in, what it found, and where the limits are.</p>
                </div>
            </div>
            <div class="fm-steps">{cards}</div>
        </section>
        """)


def _features() -> None:
    features = [
        {
            "icon": "layers",
            "label": "REASONING",
            "title": "Ranked, not guessed",
            "copy": "Possible causes are ordered by plausibility with a quick, safe test to tell them apart.",
            "visual": '<div class="fm-mini-bars"><span style="width:82%"></span><span style="width:56%"></span><span style="width:34%"></span></div>',
        },
        {
            "icon": "scan",
            "label": "VISION",
            "title": "Inspect visible damage",
            "copy": "Upload clear photos for a visual pass that separates what is visible from what a camera cannot tell.",
            "visual": '<div class="fm-mini-scan"><span></span></div>',
        },
        {
            "icon": "shield",
            "label": "SAFETY",
            "title": "Guardrails stay on",
            "copy": "A deterministic safety layer can escalate, withhold risky steps, and block live-work guidance.",
            "visual": '<div class="fm-mini-rules"><span>live work</span><b>blocked</b><span>high voltage</span><b>blocked</b></div>',
        },
        {
            "icon": "chat",
            "label": "CONTEXT",
            "title": "Ask better follow-ups",
            "copy": "Clarify a step, request simpler language, or prepare the right questions for a technician.",
            "visual": '<div class="fm-mini-chat"><span class="left"></span><span class="right"></span><span class="left short"></span></div>',
        },
        {
            "icon": "database",
            "label": "LOCAL-FIRST",
            "title": "History without accounts",
            "copy": "Sessions are saved to a local SQLite file for quick recall, search and comparison.",
            "visual": '<div class="fm-mini-db"><span>local</span><span class="fm-mini-db-dot"></span><span>sqlite</span></div>',
        },
        {
            "icon": "gauge",
            "label": "HONESTY",
            "title": "Uncertainty stated",
            "copy": "Confidence and missing evidence are part of the report — never buried in fine print.",
            "visual": '<div class="fm-mini-confidence"><span></span><span></span><span class="dim"></span></div>',
        },
    ]
    cards = "".join(
        f"""
        <article class="fm-feature-card">
            <div class="fm-feature-head">
                <span class="fm-icon-tile">{icon(feature['icon'], 22)}</span>
                <span class="fm-feature-label">{feature['label']}</span>
            </div>
            <h3>{feature['title']}</h3>
            <p>{feature['copy']}</p>
            {feature['visual']}
        </article>
        """
        for feature in features
    )
    html_block(
        f"""
        <section class="fm-features">
            <div class="fm-section-head">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>SYSTEM CAPABILITIES</span>
                <div class="fm-section-title-row">
                    <h2>Built like an instrument,<br>not a magic box.</h2>
                    <p class="fm-section-copy">Structured output, visible uncertainty and hard safety boundaries —
                    designed for decisions that involve expensive or dangerous hardware.</p>
                </div>
            </div>
            <div class="fm-feature-grid">{cards}</div>
        </section>
        """)


def _safety() -> None:
    html_block(
        f"""
        <section class="fm-safety">
            <div class="fm-safety-copy">
                <span class="fm-eyebrow fm-eyebrow-warn"><span class="fm-eyebrow-mark"></span>ENGINEERED FOR CAUTION</span>
                <h2>A fast answer should never outrun safety.</h2>
                <p>FixMate distinguishes basic, de-energized checks from repairs that require a qualified technician.
                Hazard patterns can force a professional referral and remove risky advanced steps from the report.</p>
                <div class="fm-hazard-chips">
                    <span>{icon("bolt", 13)} Mains voltage</span>
                    <span>{icon("thermometer", 13)} Swollen cells</span>
                    <span>{icon("activity", 13)} Refrigerants</span>
                    <span>{icon("alert", 13)} Thermal damage</span>
                </div>
            </div>
            <div class="fm-safety-rules">
                <div class="fm-safety-rule">
                    <span class="fm-safety-rule-icon">{icon("shield", 20)}</span>
                    <div><b>No live-work guidance</b><p>Unplug first. Internal measurement and capacitor work are technician territory.</p></div>
                </div>
                <div class="fm-safety-rule">
                    <span class="fm-safety-rule-icon">{icon("alert", 20)}</span>
                    <div><b>Hazard escalation</b><p>Burning smells, damaged batteries, gas or refrigerant leaks trigger a stop-work response.</p></div>
                </div>
                <div class="fm-safety-rule">
                    <span class="fm-safety-rule-icon">{icon("gauge", 20)}</span>
                    <div><b>Confidence you can read</b><p>Every report states its uncertainty, the evidence gaps, and when to stop.</p></div>
                </div>
                <div class="fm-safety-foot">Advisory system · not a substitute for an in-person inspection</div>
            </div>
        </section>
        """)


def _final_cta() -> None:
    with st.container(key="fm-home-cta"):
        html_block(
            """
            <div class="fm-final-cta">
                <div class="fm-cta-grid"></div>
                <div class="fm-cta-glow"></div>
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>READY WHEN YOU ARE</span>
                <h2>Bring the fault<br>into focus.</h2>
                <p>Start with what you can see, hear, and smell. FixMate will help you decide what is safe to check next.</p>
            </div>
            """)
        left, mid, right = st.columns([1.3, 1.2, 1.3])
        with mid:
            st.button(
                "Start a diagnostic",
                key="cta_start",
                type="primary",
                width="stretch",
                on_click=begin_diagnosis,
                args=(),
            )
        html_block(
            f'<div class="fm-cta-note">{icon("lock", 13)} API key stays server-side · History stored locally · No account</div>')


def render() -> None:
    _hero()
    _ticker()
    _devices()
    _how_it_works()
    _features()
    _safety()
    _final_cta()
