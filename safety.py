"""Deterministic safety checks layered on top of the AI assessment.

The language model is instructed to be conservative, but safety-critical
decisions should never depend on the model alone. These rules add a second,
predictable line of defence and can force a professional referral.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Hazard:
    key: str
    title: str
    level: str  # "critical" | "high" | "caution"
    message: str
    action: str


_RULES: list[tuple[str, str, str, str, str, re.Pattern[str]]] = [
    (
        "battery_swelling",
        "Swollen battery or casing",
        "critical",
        "A swollen lithium-ion battery can ignite or release toxic gases. Stop using and charging the device.",
        "Do not press, puncture, dismantle or charge the battery. Keep it away from flammable materials and have it handled by a qualified technician.",
        re.compile(r"\bswollen\b|\bswelling\b|\bbulg(?:ing|ed)\b|\bpuff(?:ed|y)\b", re.IGNORECASE),
    ),
    (
        "fire_smoke",
        "Smoke, sparks or burning",
        "critical",
        "Smoke, sparks or a burning smell can indicate an active fire risk or a failing component.",
        "Stop using the device. Disconnect power only if it is safe to reach the plug. Evacuate and call emergency services if a fire is active.",
        re.compile(
            r"\bsmoke\b|\bspark(?:s|ing)?\b|\bburn(?:ing|t|ed)?\b|\bfire\b|\bmelt(?:ed|ing)?\b|\bcharred\b",
            re.IGNORECASE,
        ),
    ),
    (
        "mains_shock",
        "High-voltage or mains exposure",
        "high",
        "The described work can involve mains voltage, stored capacitor charge, or exposed conductors.",
        "Do not open the enclosure or touch internal components. Unplug the device and have this work performed by a qualified technician.",
        re.compile(
            r"\bcapacitors?\b|\bmains\b|\blive (?:wire|circuit|voltage)\b|\bexposed (?:wire|wiring|conductor)s?\b|"
            r"\belectric(?:al)? shock\b|\bhigh[- ]voltage\b|\benergized\b",
            re.IGNORECASE,
        ),
    ),
    (
        "refrigerant_gas",
        "Refrigerant or gas system",
        "critical",
        "Refrigerant and fuel-gas systems are sealed, pressurised systems. Handling them without certification is dangerous and often illegal.",
        "Do not puncture, open, charge or vent the system. Ventilate the area, avoid flames and switches, and contact a licensed technician.",
        re.compile(
            r"\brefrigerant\b|\bfreon\b|\bgas leak\b|\bgas smell\b|\bammonia\b|\bcarbon monoxide\b",
            re.IGNORECASE,
        ),
    ),
    (
        "liquid_electronics",
        "Liquid near electronics",
        "caution",
        "Liquid inside an electronic device can cause corrosion or a short circuit, even after it appears dry.",
        "Keep the device unplugged and switched off. Do not charge it. Have it assessed by a technician before applying power.",
        re.compile(
            r"\bwater damage\b|\bliquid (?:spill|damage|exposure)\b|\bspilled? (?:water|liquid)\b|"
            r"\bsoaked\b|\bwater leak(?:s|ing)?\b|\bleak(?:s|ing)?\b",
            re.IGNORECASE,
        ),
    ),
]

# Arabic / Central Kurdish hazard words, so non-English descriptions still trigger the safety layer.
_DIACRITICS = re.compile("[\u064b-\u065f\u0670\u0640]")
_LETTERS = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه"})


def _norm(text: str) -> str:
    return _DIACRITICS.sub("", str(text)).translate(_LETTERS)


_MULTILINGUAL = {
    "battery_swelling": "انتفاخ|منتفخ|منتفخة|تضخم|ئاوسان|ئاوساو|ئاوسا",
    "fire_smoke": "دخان|شرر|شرارة|حريق|حرائق|احتراق|يحترق|رائحة حرق|رائحة احتراق|ذاب|ذوبان|دووکەڵ|بریسکە|بروسکە|ئاگر|سووتان|سووتا|سوتا|توایەوە|توانەوە",
    "mains_shock": "صعق|صدمة كهربائية|مكثف|جهد عالي|تيار عالي|اسلاك مكشوفة|أسلاك مكشوفة|کارەبای بەرز|کەپاسیتەر|وایەری ڕووت|کارەبا لێدان|کارەبا گرتن",
    "refrigerant_gas": "فريون|تسرب غاز|رائحة غاز|أمونيا|أول أكسيد الكربون|فریۆن|لێکچوونی گاز|بۆنی گاز|ئەمۆنیا",
    "liquid_electronics": "تسرب|سائل|بلل|مبلل|غرق|وقع في الماء|لێکچوون|شلە|تەڕ بووە|تەڕبوون|کەوتە ناو ئاو",
}
_RULES = [
    (*rule[:5], re.compile(rule[5].pattern + "|" + _norm(_MULTILINGUAL[rule[0]]), re.IGNORECASE))
    if rule[0] in _MULTILINGUAL
    else rule
    for rule in _RULES
]


_UNSAFE_PATTERNS = [
    re.compile(r"\b(?:discharge|probe|measure|test)\b[^.]{0,45}\bcapacitors?\b", re.IGNORECASE),
    re.compile(r"\b(?:work on|test|probe|touch)\b[^.]{0,35}\b(?:live|energized)\b", re.IGNORECASE),
    re.compile(r"\b(?:bypass|jumper|disable|defeat)\b[^.]{0,35}\b(?:safety|interlock|thermal fuse|ground)\b", re.IGNORECASE),
    re.compile(
        r"\brefrigerant\b[^.]{0,40}\b(?:add|recharge|charge|handle|vent|top up)\b|"
        r"\b(?:add|recharge|charge|vent)\b[^.]{0,40}\brefrigerant\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:puncture|pierce|compress|open|crush)\b[^.]{0,30}\bbattery\b", re.IGNORECASE),
]

_NEGATIONS = re.compile(r"\b(?:do not|don't|never|avoid|must not|should not)\b", re.IGNORECASE)
_URGENCY_ORDER = {"routine": 0, "soon": 1, "urgent": 2}


def scan_hazards(text: str, signs: Iterable[str] = (), category_id: str | None = None) -> list[Hazard]:
    """Return deterministic hazard findings from free text and selected signs."""
    blob = _norm(" ".join([text or "", *[str(sign) for sign in signs]]))
    if category_id == "other":
        blob += " other device"

    found: list[Hazard] = []
    for key, title, level, message, action, pattern in _RULES:
        if pattern.search(blob):
            found.append(Hazard(key=key, title=title, level=level, message=message, action=action))
    return found


def hazard_level(hazards: Iterable[Hazard]) -> str:
    levels = {hazard.level for hazard in hazards}
    if "critical" in levels:
        return "critical"
    if "high" in levels:
        return "high"
    if "caution" in levels:
        return "caution"
    return "none"


def requires_acknowledgement(hazards: Iterable[Hazard]) -> bool:
    return any(hazard.level in {"critical", "high", "caution"} for hazard in hazards)


def mandatory_professional(hazards: Iterable[Hazard]) -> bool:
    return any(hazard.level in {"critical", "high"} for hazard in hazards)


def suppress_advanced_steps(hazards: Iterable[Hazard]) -> bool:
    return any(hazard.level in {"critical", "high"} for hazard in hazards)


def prompt_directive(hazards: Iterable[Hazard]) -> str:
    hazards = list(hazards)
    if not hazards:
        return (
            "No deterministic hazard rule fired, but remain conservative. Never suggest live electrical work, "
            "capacitor discharge, refrigerant handling, or opening sealed high-voltage enclosures."
        )

    lines = [
        "The safety layer detected the following hazards. Treat them as hard constraints:",
    ]
    for hazard in hazards:
        lines.append(f"- [{hazard.level.upper()}] {hazard.title}: {hazard.action}")
    lines.append(
        "Set professional_repair.recommended to true. Keep safe_checks limited to actions a non-technician can "
        "perform without opening the device. Do not provide internal repair steps for these hazards."
    )
    return "\n".join(lines)


def _unsafe(step_text: str) -> bool:
    if _NEGATIONS.search(step_text):
        return False
    return any(pattern.search(step_text) for pattern in _UNSAFE_PATTERNS)


def apply_guardrails(report: dict, hazards: list[Hazard]) -> tuple[dict, list[str], bool]:
    """Apply deterministic overrides and remove unsafe suggested actions.

    Returns the adjusted report, human-readable notices, and whether advanced
    steps were withheld.
    """
    safe_report = copy.deepcopy(report)
    notices: list[str] = []
    blocked_count = 0

    for collection in ("safe_checks", "advanced_steps"):
        steps = safe_report.get(collection)
        if not isinstance(steps, list):
            continue
        kept = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            combined = " ".join(str(step.get(key, "")) for key in ("title", "detail", "step", "expected"))
            if _unsafe(combined):
                blocked_count += 1
                continue
            kept.append(step)
        safe_report[collection] = kept

    if blocked_count:
        notices.append(
            "The safety layer removed one or more suggested actions that could put you near live voltage, "
            "pressurised refrigerant, or a damaged battery."
        )

    professional = safe_report.get("professional_repair")
    if not isinstance(professional, dict):
        professional = {"recommended": False, "urgency": "routine", "reason": ""}
        safe_report["professional_repair"] = professional

    forced = mandatory_professional(hazards)
    if forced:
        professional["recommended"] = True
        current_urgency = str(professional.get("urgency", "routine")).lower()
        target = "urgent" if hazard_level(hazards) == "critical" else "soon"
        if _URGENCY_ORDER.get(current_urgency, 0) < _URGENCY_ORDER[target]:
            professional["urgency"] = target
        reasons = [str(professional.get("reason", "")).strip(), "This session was flagged by the safety layer."]
        professional["reason"] = " ".join(filter(None, reasons))

    withheld = suppress_advanced_steps(hazards)
    if withheld:
        safe_report["advanced_steps"] = []
        notices.append(
            "Advanced internal-repair steps are withheld for this hazard pattern. A qualified technician should "
            "assess the device before any enclosure is opened."
        )

    if hazards:
        notices.extend(hazard.action for hazard in hazards)

    # De-duplicate while preserving order.
    seen: set[str] = set()
    notices = [notice for notice in notices if not (notice in seen or seen.add(notice))]
    return safe_report, notices, withheld


def safety_summary(hazards: Iterable[Hazard]) -> str:
    level = hazard_level(hazards)
    return {
        "critical": "Critical hazard detected — stop use and seek qualified help.",
        "high": "High-risk condition detected — professional service required.",
        "caution": "Caution advised — keep the device powered off and avoid internal work.",
        "none": "No specific hazard rule fired. Still treat mains-powered repairs as professional work.",
    }[level]
