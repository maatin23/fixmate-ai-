"""Safety principles, capabilities, limitations and configuration notes."""

from __future__ import annotations

import streamlit as st

from components.cards import page_header
from components.icons import icon
from components.render import html_block
from config import get_ai_settings
from state import begin_diagnosis, go_history


def _safety_principles() -> None:
    principles = [
        (
            "bolt",
            "No live-work guidance",
            "FixMate does not instruct you to work on energised equipment, probe live circuits, or discharge capacitors. Mains-powered internals belong to qualified technicians.",
        ),
        (
            "alert",
            "Battery hazard escalation",
            "A swollen, punctured or overheating lithium-ion battery triggers a stop-use response. The app will not provide steps to compress, open or charge a damaged cell.",
        ),
        (
            "thermometer",
            "Refrigerant boundary",
            "Sealed refrigerant and gas systems are never presented as a DIY recharge or venting task. Leaks and strange smells route to a licensed technician.",
        ),
        (
            "shield",
            "A deterministic second layer",
            "Hazard patterns are scanned in code before the model is called. Critical or high-risk findings can force a professional referral and withhold advanced internal steps from the report.",
        ),
    ]
    cards = "".join(
        f"""
        <article class="fm-principle">
            <span class="fm-principle-icon">{icon(icon_name, 22)}</span>
            <h3>{title}</h3>
            <p>{copy}</p>
        </article>
        """
        for icon_name, title, copy in principles
    )
    html_block(
        f"""
        <section class="fm-about-section">
            <div class="fm-section-head">
                <span class="fm-eyebrow fm-eyebrow-warn"><span class="fm-eyebrow-mark"></span>SAFETY PRINCIPLES</span>
                <div class="fm-section-title-row">
                    <h2>The answer is never worth an injury.</h2>
                    <p class="fm-section-copy">Safety is enforced in two places: in the model's instructions, and in a deterministic layer that can override it.</p>
                </div>
            </div>
            <div class="fm-principle-grid">{cards}</div>
        </section>
        """
    )


def _pipeline() -> None:
    steps = [
        ("01", "Intake", "Device category, symptoms, onset, signs, error codes and free text."),
        ("02", "Hazard scan", "Deterministic patterns check for mains, battery, fire, refrigerant and liquid risks."),
        ("03", "AI assessment", "A structured JSON report ranks causes, separates check types and states uncertainty."),
        ("04", "Validation", "The response is normalised; missing safety fields fail closed, and unsafe steps are removed."),
        ("05", "Workspace", "The saved report supports visual inspection and context-aware follow-up questions."),
    ]
    rows = "".join(
        f"""
        <div class="fm-pipeline-step">
            <span class="fm-pipeline-num">{num}</span>
            <div><b>{title}</b><p>{copy}</p></div>
        </div>
        """
        for num, title, copy in steps
    )
    html_block(
        f"""
        <section class="fm-about-section">
            <div class="fm-section-head">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>THE PIPELINE</span>
                <div class="fm-section-title-row">
                    <h2>From words to a guarded report.</h2>
                    <p class="fm-section-copy">Nothing is presented as certain when it is a hypothesis. No simulated result is substituted for a failed API request.</p>
                </div>
            </div>
            <div class="fm-pipeline">{rows}</div>
        </section>
        """
    )


def _limits() -> None:
    html_block(
        f"""
        <section class="fm-about-section">
            <div class="fm-limit-grid">
                <div class="fm-limit-card fm-limit-good">
                    <span class="fm-limit-icon">{icon("check", 20)}</span>
                    <h3>What it does well</h3>
                    <ul>
                        <li>Organises symptoms into ranked, testable hypotheses.</li>
                        <li>Separates safe, de-energised checks from advanced repair work.</li>
                        <li>Describes visible damage in photos without guessing at internals.</li>
                        <li>Keeps uncertainty and stop conditions visible.</li>
                        <li>Stores reports locally for search and comparison.</li>
                    </ul>
                </div>
                <div class="fm-limit-card fm-limit-bad">
                    <span class="fm-limit-icon">{icon("alert", 20)}</span>
                    <h3>What it cannot do</h3>
                    <ul>
                        <li>Confirm a diagnosis or replace an in-person inspection.</li>
                        <li>Measure voltage, capacitance, pressure or component health.</li>
                        <li>See inside an enclosure or identify a hidden fault from a photo.</li>
                        <li>Guarantee repair time, part cost or model accuracy.</li>
                        <li>Make a hazardous repair safe through better wording.</li>
                    </ul>
                </div>
            </div>
        </section>
        """
    )


def _privacy(settings) -> None:
    api_status = "Key detected — live AI requests enabled" if settings.configured else "No key configured — AI requests are disabled"
    api_tone = "ok" if settings.configured else "off"
    html_block(
        f"""
        <section class="fm-about-section">
            <div class="fm-about-two">
                <div class="fm-about-panel">
                    <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>PRIVACY & STORAGE</span>
                    <h3>Local by default.</h3>
                    <p>Diagnostic records live in <code>data/fixmate.db</code> on the machine running the app. There are no accounts, no cross-user dashboard and no analytics service.</p>
                    <ul class="fm-about-list">
                        <li>{icon("check", 13)} Reports and intake text are saved to SQLite.</li>
                        <li>{icon("check", 13)} Uploaded photos are processed for the request and are <b>not</b> written to the database.</li>
                        <li>{icon("check", 13)} Chat history is kept in the current browser session only.</li>
                        <li>{icon("alert", 13)} Your inputs and images are sent to the configured AI provider for processing.</li>
                        <li>{icon("alert", 13)} A hosted filesystem may be ephemeral; do not treat history there as a permanent backup.</li>
                    </ul>
                </div>
                <div class="fm-about-panel">
                    <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>AI CONFIGURATION</span>
                    <h3>Real API, no theatre.</h3>
                    <p>FixMate uses the official OpenAI Python SDK. If the key is missing, invalid, rate-limited or the service is unreachable, the app shows the failure and does not manufacture a report.</p>
                    <div class="fm-config-rows">
                        <div><span>Provider</span><b>OpenAI</b></div>
                        <div><span>Text model</span><b>{settings.model}</b></div>
                        <div><span>Vision model</span><b>{settings.vision_model}</b></div>
                        <div><span>API status</span><b class="fm-api-{api_tone}">{api_status}</b></div>
                    </div>
                    <p class="fm-about-small">Configure with <code>OPENAI_API_KEY</code> in <code>.env</code> or Streamlit secrets. Optional: <code>OPENAI_MODEL</code>, <code>OPENAI_VISION_MODEL</code>, <code>OPENAI_BASE_URL</code>.</p>
                </div>
            </div>
        </section>
        """
    )


def _faq() -> None:
    html_block(
        """
        <section class="fm-about-section fm-faq-head">
            <div class="fm-section-head">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>QUESTIONS</span>
                <h2>What people ask before trusting a report.</h2>
            </div>
        </section>
        """
    )
    with st.expander("Is this a confirmed diagnosis?"):
        st.write(
            "No. FixMate produces ranked hypotheses from the evidence you provide. It has not measured the device. "
            "Use the report to plan safe checks and ask better questions — not as a guarantee of the fault."
        )
    with st.expander("Why does the app need an OpenAI API key?"):
        st.write(
            "Diagnosis, vision inspection and chat are live AI calls. Without a valid key the features remain unavailable by design. "
            "The app never inserts demo findings to make the interface appear functional."
        )
    with st.expander("Can I use it for mains-powered or refrigerant repairs?"):
        st.write(
            "You can use it to understand the fault and prepare questions, but it will not guide live electrical work, capacitor discharge "
            "or refrigerant handling. Those tasks require a qualified technician and the appropriate certification."
        )
    with st.expander("Where is my history stored, and can I delete it?"):
        st.write(
            "History is stored in a local SQLite database. Open History to delete individual records or clear everything. "
            "There is no cloud account or multi-user sync. On a hosted deployment, the filesystem may reset between restarts."
        )
    with st.expander("Are my photos saved?"):
        st.write(
            "No photo files are written to history. Images are resized in memory, sent to the configured vision model for the inspection, "
            "and then discarded. Only the resulting text findings are stored with the report."
        )
    with st.expander("What should I do in an emergency?"):
        st.write(
            "If there is smoke, fire, sparks or a burning smell, stop using the device, move away, and call emergency services if needed. "
            "For a swollen battery, do not charge, press or puncture it. Contact a qualified professional for safe handling."
        )


def _simple_intro() -> None:
    steps = [
        ("1", "Describe it", "Pick your device, say what is wrong, and add a photo if you like."),
        ("2", "Get a plan", "FixMate lists the most likely causes and the safe things you can check yourself."),
        ("3", "Ask more", "Chat with FixMate about your report if you want to understand it better."),
    ]
    cards = "".join(
        f"""
        <article class="fm-principle">
            <span class="fm-principle-icon" style="font:800 1.3rem var(--font-display)">{num}</span>
            <h3>{title}</h3>
            <p>{copy}</p>
        </article>
        """
        for num, title, copy in steps
    )
    html_block(
        f"""
        <section class="fm-about-section">
            <div class="fm-section-head">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>THE SIMPLE VERSION</span>
                <div class="fm-section-title-row">
                    <h2>What is FixMate?</h2>
                    <p class="fm-section-copy">FixMate is a helper for broken gadgets. Tell it what is wrong with your phone, laptop or home appliance, and it explains what is probably causing the problem, what you can safely check yourself, and when to stop and call a professional.</p>
                </div>
            </div>
            <div class="fm-principle-grid">{cards}</div>
            <p class="fm-about-small" style="margin-top:14px">FixMate is a guide, not a repair shop. The AI can be wrong, so it shows how sure it is and warns you when something could be dangerous.</p>
        </section>
        """
    )


def _credits() -> None:
    html_block(
        """
        <section style="margin:48px 0 8px;padding:34px 24px;text-align:center;background:#0b1450;border:2px solid #fff;border-top:6px solid #ff6a1a;border-radius:8px">
            <p style="margin:0 0 22px;font:600 .8rem var(--font-mono);letter-spacing:.08em;color:#b4c2ff">MADE BY</p>
            <div style="display:flex;justify-content:center;gap:56px;flex-wrap:wrap">
                <div>
                    <p style="margin:0;font:600 .8rem var(--font-mono);color:#ffe14a">DESIGN</p>
                    <p style="margin:4px 0 0;font:800 1.7rem var(--font-display);color:#fff">Zaman Zahir</p>
                </div>
                <div>
                    <p style="margin:0;font:600 .8rem var(--font-mono);color:#ffe14a">DEVELOPMENT</p>
                    <p style="margin:4px 0 0;font:800 1.7rem var(--font-display);color:#fff">Maatin Amanj</p>
                </div>
            </div>
        </section>
        """
    )


def render() -> None:
    settings = get_ai_settings()
    page_header(
        "ABOUT FIXMATE",
        "Built to slow down<br>at the right moment.",
        "FixMate is a safety-first repair triage tool: structured AI assessment, visible uncertainty, and hard boundaries around work that should never be improvised.",
    )
    left, right = st.columns([1, 1])
    with left:
        st.button("Start a diagnosis", key="about_start", type="primary", on_click=begin_diagnosis, args=(), width="stretch")
    with right:
        st.button("Browse local history", key="about_history", on_click=go_history, width="stretch")

    html_block(
        f"""
        <div class="fm-about-statement">
            <span class="fm-about-statement-icon">{icon("shield", 30)}</span>
            <p>AI guidance can be useful and still be wrong. FixMate is designed to make that tension visible — with confidence levels, evidence limits, safety flags and stop conditions on every report.</p>
        </div>
        """
    )
    _simple_intro()
    _safety_principles()
    _pipeline()
    _limits()
    _privacy(settings)
    _faq()
    html_block(
        f"""
        <div class="fm-build-note">
            <span>{icon("cpu", 16)}</span>
            <p>Python · Streamlit · SQLite · OpenAI SDK · Pillow. Diagnostic data stays local; AI processing requires a configured provider key.</p>
        </div>
        """
    )
    _credits()
