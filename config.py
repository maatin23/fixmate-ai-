"""Central configuration for FixMate AI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")


def _read_setting(name: str, default: str = "") -> str:
    """Read a value from Streamlit secrets first, then the environment."""
    try:
        import streamlit as st

        if name in st.secrets:
            value = str(st.secrets[name]).strip()
            if value:
                return value
    except Exception:
        pass

    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class AISettings:
    api_key: str
    base_url: str | None
    model: str
    vision_model: str
    timeout_seconds: float
    diagnosis_tokens: int
    vision_tokens: int
    chat_tokens: int

    @property
    def configured(self) -> bool:
        return bool(self.api_key)


def get_ai_settings() -> AISettings:
    model = _read_setting("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
    vision_model = _read_setting("OPENAI_VISION_MODEL", model) or model
    return AISettings(
        api_key=_read_setting("OPENAI_API_KEY"),
        base_url=_read_setting("OPENAI_BASE_URL") or None,
        model=model,
        vision_model=vision_model,
        timeout_seconds=75.0,
        diagnosis_tokens=2600,
        vision_tokens=1600,
        chat_tokens=1500,
    )


def get_database_path() -> Path:
    custom = _read_setting("FIXMATE_DB_PATH")
    path = Path(custom).expanduser() if custom else DATA_DIR / "fixmate.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


DEVICE_CATEGORIES = [
    {
        "id": "smartphone",
        "label": "Smartphones",
        "short": "Phone",
        "icon": "smartphone",
        "tagline": "Power, display, charging",
        "description": "Screen faults, battery health, charging ports, cameras and connectivity.",
        "prompt_hint": "Include whether the phone was dropped, exposed to liquid, or repaired before.",
        "symptoms": [
            "Won't power on",
            "Won't charge",
            "Battery drains fast",
            "Screen damaged or glitchy",
            "Overheating",
            "No network or signal",
            "Camera or speaker issue",
            "Water exposure",
        ],
    },
    {
        "id": "laptop",
        "label": "Laptops",
        "short": "Laptop",
        "icon": "laptop",
        "tagline": "Boot, thermal, power",
        "description": "Boot failures, thermal issues, keyboards, batteries and display problems.",
        "prompt_hint": "Mention whether the charger light is on and if anything appears on an external monitor.",
        "symptoms": [
            "Won't power on",
            "Won't boot or stuck loading",
            "Battery or charging issue",
            "Fan loud or overheating",
            "Keyboard or trackpad issue",
            "Screen flicker or artifacts",
            "Unexpected shutdowns",
            "Slow performance",
        ],
    },
    {
        "id": "desktop",
        "label": "Desktop PCs",
        "short": "Desktop",
        "icon": "desktop",
        "tagline": "POST, thermals, drives",
        "description": "No-display faults, boot loops, cooling, storage and peripheral issues.",
        "prompt_hint": "Include any POST beeps, debug lights, recent upgrades, and whether the fans spin.",
        "symptoms": [
            "No display or no POST",
            "Won't boot or boot loop",
            "Unexpected shutdowns",
            "Overheating or loud fans",
            "USB or peripheral issue",
            "Storage not detected",
            "Slow performance",
            "Network issue",
        ],
    },
    {
        "id": "washing_machine",
        "label": "Washing machines",
        "short": "Washer",
        "icon": "washer",
        "tagline": "Drain, spin, leaks",
        "description": "Drainage, spinning, door locks, vibration, and water management.",
        "prompt_hint": "Add the exact error code if the display shows one, and whether the drum still turns by hand.",
        "symptoms": [
            "Won't start",
            "Won't drain",
            "Drum won't spin",
            "Water leak",
            "Loud vibration or banging",
            "Door won't lock or open",
            "Cycle stops mid-way",
            "Error code on display",
        ],
    },
    {
        "id": "refrigerator",
        "label": "Refrigerators",
        "short": "Fridge",
        "icon": "refrigerator",
        "tagline": "Cooling, frost, drainage",
        "description": "Cooling loss, frost buildup, leaks, noise, and temperature control.",
        "prompt_hint": "Note fridge and freezer temperatures, frost patterns, and whether the compressor is running.",
        "symptoms": [
            "Not cooling",
            "Freezer not freezing",
            "Frost or ice buildup",
            "Water leak",
            "Loud or clicking noise",
            "Compressor runs constantly",
            "Display or control issue",
            "Error code on display",
        ],
    },
    {
        "id": "air_conditioner",
        "label": "Air conditioners",
        "short": "AC unit",
        "icon": "air_conditioner",
        "tagline": "Cooling, airflow, drainage",
        "description": "Weak cooling, airflow, drainage, odor, and control faults.",
        "prompt_hint": "State the unit type (split, window, portable) and whether the outdoor unit runs.",
        "symptoms": [
            "Not cooling",
            "Weak airflow",
            "Water dripping or leaking",
            "Bad smell",
            "Loud noise or vibration",
            "Won't turn on",
            "Remote or control issue",
            "Error code on display",
        ],
    },
    {
        "id": "television",
        "label": "Televisions",
        "short": "TV",
        "icon": "television",
        "tagline": "Picture, sound, power",
        "description": "Panel faults, audio issues, input problems, and standby failures.",
        "prompt_hint": "Mention whether the standby light reacts, and if audio works when the picture is missing.",
        "symptoms": [
            "Won't turn on",
            "No picture but sound works",
            "No sound",
            "Lines or artifacts on screen",
            "Screen cracked or damaged",
            "Input or HDMI issue",
            "Keeps restarting",
            "Remote not responding",
        ],
    },
    {
        "id": "other",
        "label": "Other devices",
        "short": "Other",
        "icon": "plug",
        "tagline": "Small appliances & more",
        "description": "Microwaves, vacuums, audio gear, power tools, and other electronics.",
        "prompt_hint": "Describe the device and its power source so the safety checks can be tailored.",
        "symptoms": [
            "Won't power on",
            "Intermittent operation",
            "Unusual noise",
            "Overheating",
            "Physical damage",
            "Performance issue",
            "Leak or liquid issue",
            "Error indicator",
        ],
    },
]

CATEGORY_BY_ID = {item["id"]: item for item in DEVICE_CATEGORIES}

AGE_OPTIONS = ["Not sure", "Less than 1 year", "1–3 years", "4–6 years", "7–10 years", "More than 10 years"]

ONSET_OPTIONS = ["Today", "A few days ago", "About a week ago", "Several weeks ago", "Several months ago", "Not sure"]

UNUSUAL_SIGNS = [
    "Nothing unusual",
    "Burning or hot-plastic smell",
    "Smoke or sparks",
    "Swollen or bulging battery or casing",
    "Liquid or refrigerant leak",
    "Grinding or scraping noise",
    "Clicking, buzzing or humming",
    "Beeping or blinking indicator lights",
    "Error code displayed",
    "Recent impact, drop or liquid exposure",
]
