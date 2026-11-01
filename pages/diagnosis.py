"""Device intake, safe diagnosis generation, report workspace and vision inspection."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from ai_service import AIError, MISSING_KEY_MESSAGE
from components.cards import (
    error_message_block,
    page_header,
    render_callout,
    render_device_grid,
    setup_card,
    show_loader,
)
from components.chat import render_chat
from components.diagnostic_report import render_image_analysis, render_report
from components.icons import icon
from components.render import html_block
from config import (
    AGE_OPTIONS,
    CATEGORY_BY_ID,
    ONSET_OPTIONS,
    UNUSUAL_SIGNS,
    get_ai_settings,
)
from database import get_diagnostic, save_diagnostic, update_image_analysis
from diagnostic_engine import run_diagnosis
from image_analysis import MAX_FILES, prepare_uploads, run_image_analysis
from state import (
    begin_diagnosis,
    choose_device,
    clear_device_selection,
    go_history,
    load_generated_diagnostic,
    set_flash,
)
from utils import escape, format_timestamp, severity_tone

def _reset_vision_upload() -> None:
    st.session_state.vision_upload_nonce += 1
    st.session_state.vision_error = None


def _reopen_vision() -> None:
    st.session_state.vision_reopen = True
    st.session_state.vision_error = None


def _close_vision_upload() -> None:
    st.session_state.vision_reopen = False


def _stepper(active: int) -> None:
    steps = [
        ("01", "Device", "Pick the hardware"),
        ("02", "Evidence", "Describe the fault"),
        ("03", "Report", "Review the findings"),
    ]
    rows = "".join(
        f"""
        <div class="fm-intake-step {'is-active' if index + 1 == active else 'is-done' if index + 1 < active else ''}">
            <span class="fm-intake-step-num">{num}</span>
            <div><b>{escape(title)}</b><small>{escape(copy)}</small></div>
        </div>
        """
        for index, (num, title, copy) in enumerate(steps)
    )
    html_block(f'<div class="fm-stepper">{rows}</div>')


def _device_selector() -> None:
    _stepper(1)
    page_header(
        "DIAGNOSTIC INTAKE",
        "Choose the device<br>we should inspect.",
        "Each device category asks for the signals that matter to its hardware. You can add photos after the report is generated.",
    )
    settings = get_ai_settings()
    if not settings.configured:
        html_block(setup_card())
        html_block(
            '<p class="fm-inline-note fm-setup-spacer">You can prepare the intake now. The analysis button will explain the key requirement if the API is not connected.</p>'
        )
    render_device_grid(choose_device, "diag", button_label="Select device")
    html_block(
        f'<div class="fm-inline-note">{icon("lock", 13)} Intake details are stored only in this app\'s local history when a report is generated.</div>'
    )


def _intake_header(category: dict) -> None:
    left, right = st.columns([5, 1.3], vertical_alignment="center")
    with left:
        html_block(
            f"""
            <div class="fm-intake-device">
                <span class="fm-intake-device-icon">{icon(category["icon"], 28)}</span>
                <div>
                    <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>SELECTED HARDWARE</span>
                    <h2>{escape(category["label"])}</h2>
                    <p>{escape(category["tagline"])} · {escape(category["prompt_hint"])}</p>
                </div>
            </div>
            """
        )
    with right:
        st.button("Change device", key="diag_change_device", on_click=clear_device_selection, width="stretch")


def _validate(description: str, manufacturer: str, model: str) -> str | None:
    if len(description.strip()) < 20:
        return "Add at least a couple of sentences describing the fault (20 characters minimum)."
    if len(manufacturer) > 80 or len(model) > 80:
        return "Manufacturer and model must each be 80 characters or fewer."
    return None


def _save_result(result: dict, inputs: dict) -> dict:
    settings = get_ai_settings()
    try:
        diagnostic_id = save_diagnostic(
            category=inputs["category"],
            manufacturer=inputs["manufacturer"],
            model=inputs["model"],
            age_range=inputs["age_range"],
            description=inputs["description"],
            symptoms=inputs["symptoms"],
            onset=inputs["onset"],
            unusual_signs=inputs["unusual_signs"],
            error_code=inputs["error_code"],
            report=result["report"],
            hazards=result["hazards"],
            safety_notices=result["safety_notices"],
            advanced_withheld=result["advanced_withheld"],
            ai_model=settings.model,
        )
        saved = get_diagnostic(diagnostic_id)
        if saved:
            set_flash("success", "Diagnostic generated and saved to local history.")
            return saved
    except Exception:
        pass

    set_flash(
        "warning",
        "The report was generated but could not be written to local history. It remains available in this session only.",
    )
    return {
        "id": None,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input": {**inputs, "category_label": CATEGORY_BY_ID.get(inputs["category"], {}).get("label", inputs["category"])},
        "report": result["report"],
        "hazards": result["hazards"],
        "safety_notices": result["safety_notices"],
        "advanced_withheld": result["advanced_withheld"],
        "image_analysis": None,
        "model": settings.model,
        "severity": result["report"].get("severity", "moderate"),
        "difficulty": result["report"].get("difficulty", ""),
        "professional_recommended": bool((result["report"].get("professional_repair") or {}).get("recommended")),
        "professional_urgency": (result["report"].get("professional_repair") or {}).get("urgency", "routine"),
    }


def _intake_form(category: dict) -> None:
    _stepper(2)
    _intake_header(category)
    settings = get_ai_settings()

    if not settings.configured:
        render_callout(
            "warn",
            "lock",
            "Live AI connection required",
            "No OpenAI API key is configured. Add OPENAI_API_KEY to a local .env file or to Streamlit secrets, then restart the app. FixMate does not generate placeholder reports.",
            raw_body=False,
        )

    form_key = f"intake_form_{category['id']}_{st.session_state.diagnosis_form_nonce}"
    left, right = st.columns([1.72, 0.82], gap="large")

    with left:
        with st.form(form_key, clear_on_submit=False):
            html_block('<div class="fm-form-section-label">Device identity</div>')
            id_a, id_b = st.columns(2, gap="medium")
            with id_a:
                manufacturer = st.text_input(
                    "Manufacturer",
                    key=f"manufacturer_{form_key}",
                    placeholder="e.g. Samsung, Dell, LG",
                    max_chars=80,
                )
            with id_b:
                model = st.text_input(
                    "Model",
                    key=f"model_{form_key}",
                    placeholder="e.g. Galaxy S22, XPS 13",
                    max_chars=80,
                )

            meta_a, meta_b, meta_c = st.columns([1, 1, 1], gap="medium")
            with meta_a:
                age_range = st.selectbox("Approximate age", AGE_OPTIONS, key=f"age_{form_key}")
            with meta_b:
                onset = st.selectbox("When it started", ONSET_OPTIONS, key=f"onset_{form_key}")
            with meta_c:
                error_code = st.text_input(
                    "Error code / display text",
                    key=f"error_{form_key}",
                    placeholder="Optional",
                    max_chars=60,
                )

            st.divider()
            html_block('<div class="fm-form-section-label">Observed symptoms</div>')
            symptoms = st.multiselect(
                "What is the device doing?",
                options=category["symptoms"],
                max_selections=6,
                accept_new_options=True,
                placeholder="Select one or more symptoms (up to 6)",
                key=f"symptoms_{form_key}",
                help="Choose the closest matches. You can type a custom symptom if it is not listed.",
            )
            signs = st.multiselect(
                "Any unusual signs?",
                options=UNUSUAL_SIGNS,
                default=[],
                max_selections=5,
                accept_new_options=True,
                placeholder="Select anything you have noticed",
                key=f"signs_{form_key}",
                help="These selections are checked by the deterministic safety layer before the report is shown.",
            )

            st.divider()
            html_block('<div class="fm-form-section-label">Your description</div>')
            description = st.text_area(
                "Describe the fault",
                key=f"description_{form_key}",
                placeholder=(
                    f"What changed? When did it start? What happens when you try to use it? "
                    f"{category['prompt_hint']}"
                ),
                height=150,
                max_chars=2000,
                help="Include anything you have already tried. Do not open the device to gather information.",
            )

            html_block(
                f"""
                <div class="fm-form-safety">
                    {icon("shield", 16)}
                    <p><b>Before you inspect:</b> unplug the device and let it cool. Do not open mains-powered equipment or touch capacitors. If you notice smoke, sparks, a burning smell, or a swollen battery, stop and seek qualified help.</p>
                </div>
                """
            )

            submitted = st.form_submit_button(
                "Generate diagnostic report",
                type="primary",
                width="stretch",
            )

        if submitted:
            error = _validate(description, manufacturer, model)
            if error:
                st.session_state.diagnosis_error = error
            elif not settings.configured:
                st.session_state.diagnosis_error = MISSING_KEY_MESSAGE
            else:
                inputs = {
                    "category": category["id"],
                    "manufacturer": manufacturer.strip(),
                    "model": model.strip(),
                    "age_range": age_range,
                    "description": description.strip(),
                    "symptoms": list(symptoms),
                    "onset": onset,
                    "unusual_signs": list(signs),
                    "error_code": error_code.strip(),
                }
                st.session_state.diagnosis_error = None
                loader_slot = st.empty()
                show_loader(
                    loader_slot,
                    "Mapping fault signatures",
                    "Weighing the evidence, ranking causes and applying the safety layer",
                )
                try:
                    result = run_diagnosis(inputs)
                except AIError as exc:
                    st.session_state.diagnosis_error = exc.message
                except Exception:
                    st.session_state.diagnosis_error = (
                        "An unexpected error stopped the diagnosis. Nothing was saved. Please retry."
                    )
                else:
                    diagnostic = _save_result(result, inputs)
                    load_generated_diagnostic(diagnostic)
                    st.rerun()
                finally:
                    loader_slot.empty()

        if st.session_state.diagnosis_error:
            html_block(
                error_message_block(
                    st.session_state.diagnosis_error,
                    title="Report generation did not complete.",
                )
            )

    with right:
        html_block(
            f"""
            <aside class="fm-intake-aside">
                <div class="fm-aside-card">
                    <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>WHAT HAPPENS NEXT</span>
                    <div class="fm-aside-step"><span>01</span><p>Your description is scanned for hazard patterns before the model is called.</p></div>
                    <div class="fm-aside-step"><span>02</span><p>The report ranks possible causes and separates basic checks from advanced work.</p></div>
                    <div class="fm-aside-step"><span>03</span><p>You can upload photos for a visible-damage pass and ask follow-up questions.</p></div>
                </div>
                <div class="fm-aside-card fm-aside-trust">
                    <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>BOUNDARIES</span>
                    <p>{icon("check", 13)} Advisory, never a confirmed diagnosis</p>
                    <p>{icon("check", 13)} No live electrical work instructions</p>
                    <p>{icon("check", 13)} No refrigerant handling guidance</p>
                    <p>{icon("check", 13)} Local storage, no account</p>
                </div>
                <p class="fm-aside-foot">Photos are never written to the history database. Only the resulting visible-finding text is stored.</p>
            </aside>
            """
        )


def _render_vision_tab(diagnostic: dict) -> None:
    analysis = diagnostic.get("image_analysis")
    settings = get_ai_settings()

    if not settings.configured:
        html_block(setup_card())
    if analysis and not st.session_state.vision_reopen:
        render_image_analysis(analysis)
        action_a, _ = st.columns([1.1, 3])
        with action_a:
            st.button("Inspect new photos", key="vision_reopen_btn", on_click=_reopen_vision, width="stretch")
        return

    html_block(
        f"""
        <div class="fm-vision-intro">
            <div class="fm-vision-intro-copy">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>VISUAL EVIDENCE</span>
                <h3>Add clear photos of the visible condition.</h3>
                <p>Use 1–{MAX_FILES} photos taken in good light. The analysis describes visible evidence only and states what a camera cannot determine. Do not open an enclosure or move a damaged battery to take a photo.</p>
                <div class="fm-vision-chips">
                    <span>{icon("image", 13)} JPG · PNG · WebP</span>
                    <span>{icon("gauge", 13)} Max 10 MB each</span>
                    <span>{icon("lock", 13)} Not saved to history</span>
                </div>
            </div>
            <span class="fm-vision-scan-visual">{icon("scan", 54)}</span>
        </div>
        """
    )

    upload_key = f"vision_upload_{diagnostic.get('id') or 'draft'}_{st.session_state.vision_upload_nonce}"
    files = st.file_uploader(
        "Device photos",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key=upload_key,
        help="Drag and drop clear photos. Avoid including serial numbers, faces, or personal documents.",
        label_visibility="collapsed",
        max_upload_size=10,
    )

    prepared = []
    if files:
        if len(files) > MAX_FILES:
            st.warning(
                f"Only the first {MAX_FILES} photos are inspected in one pass. Remove the extras and add them in a new pass if needed."
            )
        prepared, errors = prepare_uploads(files)
        for error in errors:
            st.warning(error)
        if prepared:
            preview_cols = st.columns(len(prepared), gap="small")
            for col, image in zip(preview_cols, prepared):
                with col:
                    st.image(image.data, width="stretch")
                    html_block(
                        f'<div class="fm-vision-preview-meta"><b>{escape(image.name)}</b>'
                        f"<span>{image.width}×{image.height} · {image.prepared_kb} KB</span></div>"
                    )

    if st.session_state.vision_error:
        html_block(error_message_block(st.session_state.vision_error))

    if analysis:
        html_block('<div class="fm-inline-note">Existing visible-finding results are shown below. Replacing them creates new findings for this session.</div>')
        render_image_analysis(analysis)

    action_a, action_b, action_c, _ = st.columns([1.3, 1, 1.1, 1.6])
    with action_a:
        run_clicked = st.button(
            f"Analyze {len(prepared) if prepared else ''} photo{'s' if len(prepared) != 1 else ''}".strip(),
            key="vision_run",
            type="primary",
            disabled=not prepared or not settings.configured,
            width="stretch",
        )
    with action_b:
        st.button("Clear uploads", key="vision_clear", on_click=_reset_vision_upload, width="stretch")
    with action_c:
        if analysis:
            st.button("Keep previous findings", key="vision_cancel_reopen", on_click=_close_vision_upload, width="stretch")
    if not settings.configured:
        html_block('<p class="fm-inline-note">Visual inspection requires a configured OpenAI vision model.</p>')
    elif not prepared:
        html_block('<p class="fm-inline-note">Add at least one photo to start the visual inspection.</p>')

    if run_clicked and prepared and settings.configured:
        st.session_state.vision_error = None
        loader_slot = st.empty()
        show_loader(
            loader_slot,
            "Inspecting visible condition",
            "Reviewing each photo for damage, wear and unsafe signs — without guessing at hidden faults",
        )
        try:
            inspected = run_image_analysis(prepared, diagnostic)
        except AIError as exc:
            st.session_state.vision_error = exc.message
        except Exception:
            st.session_state.vision_error = (
                "An unexpected error interrupted the visual inspection. Nothing was saved. Please retry."
            )
        else:
            diagnostic["image_analysis"] = inspected
            st.session_state.current_diagnostic = diagnostic
            if diagnostic.get("id"):
                update_image_analysis(int(diagnostic["id"]), inspected)
            st.session_state.vision_upload_nonce += 1
            st.session_state.vision_reopen = False
            set_flash("success", "Visual inspection complete. Findings were added to this session.")
            st.rerun()
        finally:
            loader_slot.empty()


def _session_toolbar(diagnostic: dict) -> None:
    left, right = st.columns([5, 2.4], vertical_alignment="center")
    with left:
        session_id = diagnostic.get("id")
        html_block(
            f"""
            <div class="fm-session-meta">
                <span class="fm-session-dot"></span>
                <span>{'SAVED SESSION #' + str(int(session_id)).zfill(4) if session_id else 'UNSAVED SESSION'}</span>
                <span class="fm-session-sep"></span>
                <span>{escape(format_timestamp(diagnostic.get("created_at")))}</span>
                <span class="fm-session-sep"></span>
                <span>{escape(diagnostic.get("model") or 'model unknown')}</span>
            </div>
            """
        )
    with right:
        new_col, history_col = st.columns(2, gap="small")
        with new_col:
            st.button("New diagnosis", key="session_new", on_click=begin_diagnosis, args=(), width="stretch")
        with history_col:
            st.button("History", key="session_history", on_click=go_history, width="stretch")


def _session_header(diagnostic: dict) -> None:
    inputs = diagnostic.get("input") or {}
    report = diagnostic.get("report") or {}
    category = CATEGORY_BY_ID.get(inputs.get("category", ""), {})
    brand = " ".join(filter(None, [inputs.get("manufacturer", ""), inputs.get("model", "")])).strip()
    device = f"{brand}" if brand else (inputs.get("category_label") or "Unknown device")
    severity = str(report.get("severity") or diagnostic.get("severity") or "moderate")
    severity_class = severity_tone(severity)
    professional = report.get("professional_repair") or {}
    confidence = str(report.get("confidence", "low")).lower()
    confidence_tone = "strong" if confidence == "high" else "medium" if confidence == "medium" else "weak"
    tags = [
        f'<span class="fm-tag fm-tag-{severity_class}">{escape(severity.title())} severity</span>',
        f'<span class="fm-tag fm-tag-{confidence_tone}">{escape(confidence.title())} confidence</span>',
    ]
    if professional.get("recommended"):
        tags.append('<span class="fm-tag fm-tag-high">Professional referral</span>')
    if diagnostic.get("advanced_withheld"):
        tags.append('<span class="fm-tag fm-tag-critical">Advanced steps withheld</span>')
    if diagnostic.get("image_analysis"):
        tags.append('<span class="fm-tag fm-tag-neutral">Photos inspected</span>')

    html_block(
        f"""
        <header class="fm-session-hero">
            <span class="fm-session-hero-icon">{icon(category.get("icon", "chip"), 34)}</span>
            <div class="fm-session-hero-main">
                <span class="fm-eyebrow"><span class="fm-eyebrow-mark"></span>DIAGNOSTIC WORKSPACE</span>
                <h1>{escape(device)}</h1>
                <p>{escape(inputs.get("category_label", "Device"))}{f" · {escape(inputs.get('age_range', ''))}" if inputs.get('age_range') else ""}{f" · Onset: {escape(inputs.get('onset', ''))}" if inputs.get('onset') else ""}</p>
                <div class="fm-session-tags">{''.join(tags)}</div>
            </div>
            <div class="fm-session-hero-side">
                <span>SESSION TYPE</span>
                <b>{'Saved locally' if diagnostic.get('id') else 'Session only'}</b>
                <span>REPORT BASIS</span>
                <b>Description + intake signals</b>
            </div>
        </header>
        """
    )


def _workspace(diagnostic: dict) -> None:
    _stepper(3)
    _session_toolbar(diagnostic)
    _session_header(diagnostic)

    report_tab, vision_tab, chat_tab = st.tabs(
        ["Diagnostic report", "Vision inspection", "Follow-up chat"],
        key="fm-report-tabs",
        default="Diagnostic report",
    )
    with report_tab:
        render_report(diagnostic)
    with vision_tab:
        _render_vision_tab(diagnostic)
    with chat_tab:
        render_chat(diagnostic, page_key="diag")


def render() -> None:
    diagnostic = st.session_state.get("current_diagnostic")
    if diagnostic:
        _workspace(diagnostic)
        return

    category_id = st.session_state.get("selected_device")
    if not category_id or category_id not in CATEGORY_BY_ID:
        st.session_state.selected_device = None
        _device_selector()
        return

    _intake_form(CATEGORY_BY_ID[category_id])
