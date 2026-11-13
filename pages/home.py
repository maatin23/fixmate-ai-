"""Landing page: hero with a report preview, stats, device picker, steps, features, trust band, FAQ."""

from __future__ import annotations

import streamlit as st

from components.cards import render_device_grid
from components.icons import icon
from components.render import html_block
from i18n import t
from state import begin_diagnosis


def _head(kicker: str, title: str, copy: str, anchor: str = "") -> None:
    html_block(
        f"""
        <div class="pf-head" id="{anchor}">
            <span class="pf-kicker">{kicker}</span>
            <h2>{title}</h2>
            <p>{copy}</p>
        </div>
        """
    )


def _hero() -> None:
    left, right = st.columns([1.05, 1], gap="large", vertical_alignment="center")
    with left:
        html_block(
            """
            <div class="pf-hero">
                <span class="pf-badge"><span class="pf-dot"></span>Safety-first repair assistant</span>
                <h1>Find out what's wrong with your device, safely.</h1>
                <p class="pf-lead">Describe the problem or add a photo. FixMate ranks the likely causes, separates safe checks from advanced repairs, and tells you when to call a professional.</p>
            </div>
            """
        )
        first, second = st.columns(2, gap="small")
        with first:
            st.button(t("Start diagnosis"), key="hero_start", type="primary", width="stretch", on_click=begin_diagnosis, args=())
        with second:
            html_block('<a class="pf-ghost" href="#how-it-works">See how it works</a>')
        html_block(
            """
            <ul class="pf-trust">
                <li>No account needed</li>
                <li>16 device types</li>
                <li>English, Kurdish and Arabic</li>
            </ul>
            """
        )
    with right:
        html_block(
            f"""
            <div class="pf-preview" aria-label="Example diagnostic report">
                <div class="pf-pv-head">
                    <span class="pf-pv-icon">{icon("smartphone", 20)}</span>
                    <div><b>iPhone 14</b><small>Won't charge</small></div>
                    <span class="pf-pill">Medium risk</span>
                </div>
                <div class="pf-pv-body">
                    <h4>Most likely causes</h4>
                    <div class="pf-row"><span>Charging port debris</span><div class="pf-bar"><i style="--w:78%"></i></div><em>78%</em></div>
                    <div class="pf-row"><span>Faulty cable or adapter</span><div class="pf-bar"><i style="--w:46%"></i></div><em>46%</em></div>
                    <div class="pf-row"><span>Battery wear</span><div class="pf-bar"><i style="--w:24%"></i></div><em>24%</em></div>
                    <h4 style="margin-top:18px">Safe checks first</h4>
                    <ol>
                        <li>Try another cable and a wall adapter.</li>
                        <li>Look into the port with a torch for lint.</li>
                        <li>Restart the phone.</li>
                    </ol>
                    <div class="pf-pv-foot">{icon("shield", 16)}<span>Advanced steps are withheld when something looks unsafe.</span></div>
                </div>
            </div>
            """
        )


def _stats() -> None:
    items = [("16", "Device types"), ("1,400+", "Models and series"), ("3", "Languages"), ("0", "Sign-ups needed")]
    cells = "".join(f'<div class="pf-stat"><b>{value}</b><span>{label}</span></div>' for value, label in items)
    html_block(f'<div class="pf-stats">{cells}</div>')


def _devices() -> None:
    _head("Devices", "Choose your device", "Pick what is broken. FixMate adapts the questions to that device.", "devices")
    render_device_grid(begin_diagnosis, "home")


def _how_it_works() -> None:
    steps = [
        ("1", "Describe the fault", "Pick your device, brand and model, then choose the symptoms. Add a photo if it helps."),
        ("2", "Read the report", "You get ranked causes, safe checks first, and a clear note on how sure the AI is."),
        ("3", "Fix it or get help", "Follow the safe steps, ask follow-up questions, or find a repair shop near you."),
    ]
    cards = "".join(
        f'<div class="pf-step"><span class="pf-step-n">{n}</span><h3>{title}</h3><p>{copy}</p></div>'
        for n, title, copy in steps
    )
    _head("How it works", "From symptom to a safer next step", "Three simple steps, and no account.", "how-it-works")
    html_block(f'<div class="pf-steps">{cards}</div>')


def _features() -> None:
    items = [
        ("shield", "Safety guardrails", "Dangerous situations like swollen batteries or gas leaks stop the advice and tell you what to do."),
        ("layers", "Ranked causes", "See the most likely cause first, with reasons in plain language."),
        ("eye", "Photo inspection", "Add photos and the AI describes only the damage it can really see."),
        ("chat", "Ask follow-ups", "Chat about your report and ask for simpler wording or next steps."),
        ("tune", "Guided intake", "Brand and model pickers and symptom lists make describing the problem quick."),
        ("wrench", "Repair shop finder", "One tap opens a map search for repair shops near you."),
    ]
    cards = "".join(
        f'<div class="pf-feature"><span class="pf-ic">{icon(name, 20)}</span><h3>{title}</h3><p>{copy}</p></div>'
        for name, title, copy in items
    )
    _head("Features", "Everything you need to fix with confidence", "Made for people who are not technicians.")
    html_block(f'<div class="pf-features">{cards}</div>')


def _trust() -> None:
    html_block(
        """
        <div class="pf-band">
            <div>
                <h2>Built to be careful</h2>
                <p>FixMate is advice, not a verdict. It never tells you to work on live electrical parts, and it says clearly when to stop.</p>
            </div>
            <ul>
                <li>No live electrical work</li>
                <li>Hazards trigger a stop notice</li>
                <li>Uncertainty is always shown</li>
            </ul>
        </div>
        """
    )


def _faq() -> None:
    items = [
        ("Is FixMate a replacement for a technician?", "No. It gives guidance and safe checks. For anything risky, it tells you to see a professional."),
        ("Do I need an account?", "No. There is no sign-up, and each visitor only sees their own history."),
        ("Which languages does it support?", "English, Kurdish (Sorani) and Arabic."),
        ("Can I upload photos?", "Yes. Photos are checked for visible damage only and are not saved."),
    ]
    rows = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in items)
    _head("FAQ", "Questions people ask", "")
    html_block(f'<div class="pf-faq">{rows}</div>')


def _final_cta() -> None:
    with st.container(key="pf-cta"):
        html_block("<h2>Ready to find the fault?</h2><p>It takes about two minutes and needs no account.</p>")
        _, middle, _ = st.columns([1, 1, 1])
        with middle:
            st.button(t("Start diagnosis"), key="cta_start", type="primary", width="stretch", on_click=begin_diagnosis, args=())


def render() -> None:
    _hero()
    _stats()
    _devices()
    _how_it_works()
    _features()
    _trust()
    _faq()
    _final_cta()
