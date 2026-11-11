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


def _visitor_db_path() -> Path | None:
    """Private history file for this browser session, so visitors never see each other's chats."""
    try:
        import time
        import uuid

        import streamlit as st

        sid = st.session_state.get("_fm_visitor_id")
        if not sid:
            sid = uuid.uuid4().hex
            st.session_state["_fm_visitor_id"] = sid
            folder = DATA_DIR / "sessions"
            folder.mkdir(parents=True, exist_ok=True)
            cutoff = time.time() - 24 * 3600
            for old_file in folder.glob("*.db"):  # tidy up files from old visits
                try:
                    if old_file.stat().st_mtime < cutoff:
                        old_file.unlink()
                except OSError:
                    pass
        return DATA_DIR / "sessions" / f"{sid}.db"
    except Exception:
        return None


def get_database_path() -> Path:
    custom = _read_setting("FIXMATE_DB_PATH")
    if custom:
        path = Path(custom).expanduser()
    else:
        path = _visitor_db_path() or DATA_DIR / "fixmate.db"
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
        "id": "tablet",
        "label": "Tablets",
        "short": "Tablet",
        "icon": "tablet",
        "tagline": "Power, touch, battery",
        "description": "Charging faults, touch and display problems, battery wear, and boot loops.",
        "prompt_hint": "Mention the brand and whether it was dropped, got wet, or recently updated.",
        "symptoms": [
            "Won't power on",
            "Won't charge",
            "Battery drains fast",
            "Screen cracked or unresponsive",
            "Touch not working properly",
            "Overheating",
            "Wi-Fi or Bluetooth problems",
            "Stuck on logo or boot loop",
            "Camera or speaker issue",
        ],
    },
    {
        "id": "printer",
        "label": "Printers",
        "short": "Printer",
        "icon": "printer",
        "tagline": "Printing, paper, connection",
        "description": "Paper jams, poor print quality, connection drops, and ink or toner errors.",
        "prompt_hint": "Say whether it is inkjet or laser, and how it connects (USB or Wi-Fi).",
        "symptoms": [
            "Won't print",
            "Paper jams",
            "Streaky or faded prints",
            "Not detected by the computer",
            "Won't connect to Wi-Fi",
            "Error light blinking",
            "Strange noises",
            "Ink or toner not recognised",
            "Prints blank pages",
        ],
    },
    {
        "id": "game_console",
        "label": "Game consoles",
        "short": "Console",
        "icon": "game_console",
        "tagline": "Video, discs, controllers",
        "description": "No-video faults, overheating, disc and controller problems, and crashes.",
        "prompt_hint": "Mention the console model and whether the fan is loud or the lights react.",
        "symptoms": [
            "Won't power on",
            "Overheating or loud fan",
            "No video signal",
            "Disc not reading",
            "Controller not connecting",
            "Freezes or crashes",
            "Storage or update error",
            "No sound",
            "Charging or port problem",
        ],
    },
    {
        "id": "router",
        "label": "Routers",
        "short": "Router",
        "icon": "router",
        "tagline": "Internet, Wi-Fi, signal",
        "description": "Dropped connections, slow speeds, weak signal, and warning lights.",
        "prompt_hint": "Describe the light colours and whether the problem affects all devices or only one.",
        "symptoms": [
            "No internet",
            "Slow speeds",
            "Wi-Fi keeps dropping",
            "Weak signal in some rooms",
            "Lights blinking red or orange",
            "Can't open the settings page",
            "Keeps restarting",
            "Devices can't connect",
            "Overheating",
        ],
    },
    {
        "id": "microwave",
        "label": "Microwaves",
        "short": "Microwave",
        "icon": "microwave",
        "tagline": "Heating, turntable, controls",
        "description": "Heating faults, turntable problems, and control panel issues. Never open the casing.",
        "prompt_hint": "Mention whether it hums, the light works, and whether the door closes firmly.",
        "symptoms": [
            "Won't heat",
            "Turntable not spinning",
            "Sparks inside",
            "Display not working",
            "Buttons unresponsive",
            "Door won't close properly",
            "Strange noise",
            "Trips the breaker",
            "Food heats unevenly",
        ],
    },
    {
        "id": "dishwasher",
        "label": "Dishwashers",
        "short": "Dishwasher",
        "icon": "dishwasher",
        "tagline": "Drain, fill, cleaning",
        "description": "Drain and fill faults, leaks, poor cleaning, and error codes.",
        "prompt_hint": "Say what the display shows and whether water stays in the bottom after a cycle.",
        "symptoms": [
            "Won't start",
            "Won't drain",
            "Not cleaning well",
            "Leaking water",
            "Won't fill with water",
            "Dishes stay wet",
            "Strange noises",
            "Error code on display",
            "Door won't latch",
            "Bad smell",
        ],
    },
    {
        "id": "smartwatch",
        "label": "Smartwatches",
        "short": "Watch",
        "icon": "smartwatch",
        "tagline": "Battery, sync, sensors",
        "description": "Charging faults, battery wear, sync problems, and sensor errors.",
        "prompt_hint": "Mention the model and whether it has been in water or dropped.",
        "symptoms": [
            "Won't turn on",
            "Won't charge",
            "Battery drains fast",
            "Screen cracked",
            "Not syncing with phone",
            "Heart-rate sensor wrong",
            "Buttons stuck",
            "Water exposure",
        ],
    },
    {
        "id": "headphones",
        "label": "Headphones & earbuds",
        "short": "Audio",
        "icon": "headphones",
        "tagline": "Sound, pairing, charging",
        "description": "One-sided audio, pairing failures, charging faults, and microphone issues.",
        "prompt_hint": "Say whether it is wired or wireless, and which side or earbud has the problem.",
        "symptoms": [
            "One side is silent",
            "No sound at all",
            "Won't pair",
            "Won't charge",
            "Crackling or static",
            "Microphone not working",
            "Battery drains fast",
            "Charging case won't charge",
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


# Extra symptom choices for the original device types.
_EXTRA_SYMPTOMS = {
    "smartphone": ["Touch screen not responding", "Stuck on logo or boot loop", "Wi-Fi or Bluetooth problems", "Charging port loose"],
    "laptop": ["Wi-Fi or Bluetooth problems", "No sound or microphone", "USB or port not working", "Hinge or casing damage"],
    "desktop": ["Blue screen or crashes", "No sound", "Graphics card or display glitches", "Power supply clicking or burning smell"],
    "washing_machine": ["Clothes stay too wet", "Bad smell", "Too much foam or suds", "Won't fill with water"],
    "refrigerator": ["Door seal or gasket damaged", "Ice maker not working", "Light not working", "Too cold, food freezing"],
    "air_conditioner": ["Ice on the unit", "Turns off by itself", "Outdoor unit not running", "Thermostat reads wrong"],
    "television": ["No Wi-Fi or app problems", "Colours look wrong", "Backlight flickers or dim", "Black screen after a few seconds"],
    "other": ["Smells like burning", "Battery or charging problem", "Buttons or controls not working"],
}
for _category in DEVICE_CATEGORIES:
    _category["symptoms"] = _category["symptoms"] + [
        item for item in _EXTRA_SYMPTOMS.get(_category["id"], []) if item not in _category["symptoms"]
    ]

# Brand choices shown as one-tap options on the diagnosis form ("other" has none).
BRANDS_BY_CATEGORY = {
    "smartphone": ["Apple", "Samsung", "Xiaomi", "Huawei", "Oppo", "Vivo", "Honor", "Realme", "OnePlus", "Google Pixel", "Motorola", "Nokia", "Infinix", "Tecno", "Sony", "Asus"],
    "laptop": ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Microsoft Surface", "Samsung", "Huawei", "Razer", "LG", "Toshiba"],
    "desktop": ["Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Apple", "Alienware", "Custom-built PC"],
    "washing_machine": ["Samsung", "LG", "Bosch", "Siemens", "Whirlpool", "Beko", "Miele", "Electrolux", "Haier", "Hisense", "Panasonic", "Candy", "Indesit", "Ariston", "Midea"],
    "refrigerator": ["Samsung", "LG", "Bosch", "Siemens", "Whirlpool", "Beko", "Haier", "Hisense", "Panasonic", "Electrolux", "Sharp", "Midea", "Hitachi", "Toshiba", "Smeg", "Daewoo"],
    "air_conditioner": ["Gree", "Midea", "LG", "Samsung", "Daikin", "Carrier", "Haier", "Hisense", "Panasonic", "Mitsubishi", "Toshiba", "TCL", "General", "Fujitsu", "Hitachi", "York"],
    "television": ["Samsung", "LG", "Sony", "TCL", "Hisense", "Xiaomi", "Philips", "Panasonic", "Sharp", "Toshiba", "Vizio", "Skyworth", "Haier", "Huawei"],
    "tablet": ["Apple iPad", "Samsung", "Huawei", "Lenovo", "Xiaomi", "Amazon Fire", "Microsoft Surface", "Honor", "Realme", "Oppo"],
    "printer": ["HP", "Canon", "Epson", "Brother", "Samsung", "Xerox", "Lexmark", "Ricoh", "Kyocera", "Konica Minolta", "Pantum", "OKI"],
    "game_console": ["Sony PlayStation", "Microsoft Xbox", "Nintendo", "Valve Steam Deck", "Asus ROG Ally", "Meta Quest"],
    "router": ["TP-Link", "Huawei", "Netgear", "D-Link", "Asus", "Xiaomi", "ZTE", "Linksys", "Tenda", "Mercusys", "Zyxel", "MikroTik", "Ubiquiti", "Cisco", "Nokia"],
    "microwave": ["Samsung", "LG", "Panasonic", "Sharp", "Bosch", "Siemens", "Whirlpool", "Midea", "Toshiba", "Electrolux", "Daewoo", "Beko", "Hisense"],
    "dishwasher": ["Bosch", "Siemens", "Samsung", "LG", "Whirlpool", "Beko", "Miele", "Electrolux", "AEG", "Haier", "Hisense", "Indesit", "Candy", "Midea"],
    "smartwatch": ["Apple Watch", "Samsung Galaxy Watch", "Huawei", "Xiaomi", "Garmin", "Fitbit", "Amazfit", "Google Pixel Watch", "Honor", "Oppo", "Fossil"],
    "headphones": ["Apple AirPods", "Samsung", "Sony", "JBL", "Bose", "Xiaomi", "Huawei", "Anker Soundcore", "Beats", "Sennheiser", "Oppo", "Realme", "Jabra", "Skullcandy"],
}

# Model choices shown after a brand is picked (phones and game consoles for now; add more the same way).
MODELS_BY_BRAND = {
    "smartphone": {
        "Apple": [
                "iPhone 18 Pro Max",
                "iPhone 18 Pro",
                "iPhone Duo",
                "iPhone 17 Pro Max",
                "iPhone 17 Pro",
                "iPhone Air",
                "iPhone 17",
                "iPhone 17e",
                "iPhone 16 Pro Max",
                "iPhone 16 Pro",
                "iPhone 16 Plus",
                "iPhone 16",
                "iPhone 16e",
                "iPhone 15 Pro Max",
                "iPhone 15 Pro",
                "iPhone 15 Plus",
                "iPhone 15",
                "iPhone 14 Pro Max",
                "iPhone 14 Pro",
                "iPhone 14 Plus",
                "iPhone 14",
                "iPhone SE (3rd generation)",
                "iPhone 13 Pro Max",
                "iPhone 13 Pro",
                "iPhone 13",
                "iPhone 13 mini",
                "iPhone 12 Pro Max",
                "iPhone 12 Pro",
                "iPhone 12",
                "iPhone 12 mini",
                "iPhone SE (2nd generation)",
                "iPhone 11 Pro Max",
                "iPhone 11 Pro",
                "iPhone 11",
                "iPhone XS Max",
                "iPhone XS",
                "iPhone XR",
                "iPhone X",
                "iPhone 8 Plus",
                "iPhone 8",
                "iPhone 7 Plus",
                "iPhone 7"
        ],
        "Samsung": [
                "Galaxy Z Fold8",
                "Galaxy Z Flip8",
                "Galaxy S26 Ultra",
                "Galaxy S26+",
                "Galaxy S26",
                "Galaxy Z Fold7",
                "Galaxy Z Flip7",
                "Galaxy Z Flip7 FE",
                "Galaxy S25 Ultra",
                "Galaxy S25+",
                "Galaxy S25",
                "Galaxy S25 Edge",
                "Galaxy S25 FE",
                "Galaxy S24 Ultra",
                "Galaxy S24+",
                "Galaxy S24",
                "Galaxy S24 FE",
                "Galaxy Z Fold6",
                "Galaxy Z Flip6",
                "Galaxy S23 Ultra",
                "Galaxy S23+",
                "Galaxy S23",
                "Galaxy S23 FE",
                "Galaxy Z Fold5",
                "Galaxy Z Flip5",
                "Galaxy S22 Ultra",
                "Galaxy S22+",
                "Galaxy S22",
                "Galaxy S21 Ultra",
                "Galaxy S21+",
                "Galaxy S21",
                "Galaxy S21 FE",
                "Galaxy S20 Ultra",
                "Galaxy S20+",
                "Galaxy S20",
                "Galaxy S20 FE",
                "Galaxy Note 20 Ultra",
                "Galaxy Note 20",
                "Galaxy A57",
                "Galaxy A56",
                "Galaxy A55",
                "Galaxy A54",
                "Galaxy A53",
                "Galaxy A52",
                "Galaxy A37",
                "Galaxy A36",
                "Galaxy A35",
                "Galaxy A34",
                "Galaxy A26",
                "Galaxy A25",
                "Galaxy A16",
                "Galaxy A15",
                "Galaxy A14"
        ],
        "Xiaomi": [
                "Xiaomi 17 Ultra",
                "Xiaomi 17 Pro Max",
                "Xiaomi 17 Pro",
                "Xiaomi 17",
                "Xiaomi 15T Pro",
                "Xiaomi 15T",
                "Xiaomi 15 Ultra",
                "Xiaomi 15",
                "Xiaomi 14T Pro",
                "Xiaomi 14T",
                "Xiaomi 14 Ultra",
                "Xiaomi 14",
                "Xiaomi 13T Pro",
                "Xiaomi 13T",
                "Xiaomi 13 Ultra",
                "Xiaomi 13 Pro",
                "Xiaomi 13",
                "Xiaomi 12 Pro",
                "Xiaomi 12",
                "Redmi Note 15 Pro+",
                "Redmi Note 15 Pro",
                "Redmi Note 15",
                "Redmi Note 14 Pro+",
                "Redmi Note 14 Pro",
                "Redmi Note 14",
                "Redmi Note 13 Pro+",
                "Redmi Note 13 Pro",
                "Redmi Note 13",
                "Redmi Note 12 Pro",
                "Redmi Note 12",
                "Redmi 15",
                "Redmi 14C",
                "Redmi 13C",
                "Redmi 13",
                "Redmi 12",
                "POCO F7 Pro",
                "POCO F7",
                "POCO F6 Pro",
                "POCO F6",
                "POCO X7 Pro",
                "POCO X7",
                "POCO X6 Pro",
                "POCO X6",
                "POCO M7",
                "POCO M6"
        ],
        "Huawei": [
                "Huawei Mate 80 Pro",
                "Huawei Mate 80",
                "Huawei Pura 80 Ultra",
                "Huawei Pura 80 Pro",
                "Huawei Pura 80",
                "Huawei Mate XT",
                "Huawei Mate X6",
                "Huawei Mate 70 Pro",
                "Huawei Mate 70",
                "Huawei Pura 70 Ultra",
                "Huawei Pura 70 Pro",
                "Huawei Pura 70",
                "Huawei Mate 60 Pro",
                "Huawei Mate 60",
                "Huawei Nova 14",
                "Huawei Nova 13",
                "Huawei Nova 12",
                "Huawei Nova 11",
                "Huawei Nova 10",
                "Huawei P60 Pro",
                "Huawei P50 Pro",
                "Huawei Mate 50 Pro",
                "Huawei Mate 40 Pro",
                "Huawei Mate 30 Pro",
                "Huawei P40 Pro",
                "Huawei P30 Pro",
                "Huawei P30"
        ],
        "Oppo": [
                "Oppo Find X9 Ultra",
                "Oppo Find X9 Pro",
                "Oppo Find X9",
                "Oppo Find X8 Ultra",
                "Oppo Find X8 Pro",
                "Oppo Find X8",
                "Oppo Find N5",
                "Oppo Find N3 Flip",
                "Oppo Reno 15 Pro",
                "Oppo Reno 15",
                "Oppo Reno 14 Pro",
                "Oppo Reno 14",
                "Oppo Reno 13 Pro",
                "Oppo Reno 13",
                "Oppo Reno 12 Pro",
                "Oppo Reno 12",
                "Oppo Reno 11",
                "Oppo Reno 10",
                "Oppo A5 Pro",
                "Oppo A98",
                "Oppo A78",
                "Oppo A58",
                "Oppo A38",
                "Oppo A18"
        ],
        "Vivo": [
                "Vivo X300 Ultra",
                "Vivo X300 Pro",
                "Vivo X300",
                "Vivo X200 Ultra",
                "Vivo X200 Pro",
                "Vivo X200",
                "Vivo X100 Pro",
                "Vivo X100",
                "Vivo V60",
                "Vivo V50",
                "Vivo V40",
                "Vivo V30 Pro",
                "Vivo V30",
                "Vivo V29",
                "Vivo Y300",
                "Vivo Y200",
                "Vivo Y100",
                "Vivo Y36",
                "Vivo Y29",
                "Vivo Y28"
        ],
        "Honor": [
                "Honor Magic8 Pro",
                "Honor Magic8",
                "Honor Magic7 Pro",
                "Honor Magic7",
                "Honor Magic6 Pro",
                "Honor Magic6",
                "Honor Magic V5",
                "Honor Magic V3",
                "Honor Magic V2",
                "Honor 400 Pro",
                "Honor 400",
                "Honor 200 Pro",
                "Honor 200",
                "Honor 90",
                "Honor 70",
                "Honor X9c",
                "Honor X9b",
                "Honor X8b",
                "Honor X7b"
        ],
        "Realme": [
                "Realme GT 7 Pro",
                "Realme GT 7",
                "Realme GT 6",
                "Realme GT 5 Pro",
                "Realme 15 Pro",
                "Realme 15",
                "Realme 14 Pro+",
                "Realme 14 Pro",
                "Realme 13 Pro+",
                "Realme 13 Pro",
                "Realme 12 Pro+",
                "Realme 12 Pro",
                "Realme 12",
                "Realme 11 Pro+",
                "Realme 11",
                "Realme C75",
                "Realme C67",
                "Realme C55",
                "Realme C53",
                "Realme Narzo 80 Pro",
                "Realme Narzo 70"
        ],
        "OnePlus": [
                "OnePlus 16",
                "OnePlus 15",
                "OnePlus 15R",
                "OnePlus 13",
                "OnePlus 13R",
                "OnePlus 13s",
                "OnePlus 12",
                "OnePlus 12R",
                "OnePlus 11",
                "OnePlus 11R",
                "OnePlus 10 Pro",
                "OnePlus 10T",
                "OnePlus Open",
                "Nord 5",
                "Nord 4",
                "Nord 3",
                "Nord CE 5",
                "Nord CE 4",
                "Nord CE 3",
                "Nord N30"
        ],
        "Google Pixel": [
                "Pixel 11 Pro Fold",
                "Pixel 11 Pro XL",
                "Pixel 11 Pro",
                "Pixel 11",
                "Pixel 10 Pro Fold",
                "Pixel 10 Pro XL",
                "Pixel 10 Pro",
                "Pixel 10",
                "Pixel 9a",
                "Pixel 9 Pro Fold",
                "Pixel 9 Pro XL",
                "Pixel 9 Pro",
                "Pixel 9",
                "Pixel 8a",
                "Pixel 8 Pro",
                "Pixel 8",
                "Pixel Fold",
                "Pixel 7a",
                "Pixel 7 Pro",
                "Pixel 7",
                "Pixel 6a",
                "Pixel 6 Pro",
                "Pixel 6",
                "Pixel 5a",
                "Pixel 5",
                "Pixel 4a",
                "Pixel 4 XL",
                "Pixel 4"
        ],
        "Motorola": [
                "Razr Ultra",
                "Razr+",
                "Razr",
                "Signature",
                "Edge 60 Pro",
                "Edge 60 Fusion",
                "Edge 50 Pro",
                "Edge 50 Fusion",
                "Edge 40",
                "Moto G96",
                "Moto G86",
                "Moto G85",
                "Moto G84",
                "Moto G75",
                "Moto G73",
                "Moto G54",
                "Moto G34",
                "Moto G24",
                "Moto G15",
                "Moto G Stylus"
        ],
        "Nokia": [
                "Nokia G60 5G",
                "Nokia G42 5G",
                "Nokia G22",
                "Nokia G21",
                "Nokia G11",
                "Nokia C32",
                "Nokia C22",
                "Nokia C12",
                "Nokia X30 5G",
                "Nokia X20",
                "Nokia 110 4G",
                "Nokia 105 4G"
        ],
        "Infinix": [
                "Infinix Zero 40",
                "Infinix Zero 30",
                "Infinix Zero Ultra",
                "Infinix GT 30 Pro",
                "Infinix GT 20 Pro",
                "Infinix Note 50 Pro",
                "Infinix Note 40 Pro",
                "Infinix Note 40",
                "Infinix Hot 50",
                "Infinix Hot 40",
                "Infinix Hot 30",
                "Infinix Smart 9",
                "Infinix Smart 8"
        ],
        "Tecno": [
                "Tecno Phantom V Fold",
                "Tecno Phantom X2",
                "Tecno Camon 40 Pro",
                "Tecno Camon 30 Pro",
                "Tecno Camon 20",
                "Tecno Spark 40 Pro",
                "Tecno Spark 30 Pro",
                "Tecno Spark 20 Pro",
                "Tecno Pova 8 Pro",
                "Tecno Pova 7",
                "Tecno Pova 6 Pro",
                "Tecno Pova 5"
        ],
        "Sony": [
                "Xperia 1 VII",
                "Xperia 1 VI",
                "Xperia 1 V",
                "Xperia 1 IV",
                "Xperia 5 V",
                "Xperia 5 IV",
                "Xperia 10 VII",
                "Xperia 10 VI",
                "Xperia 10 V",
                "Xperia 10 IV",
                "Xperia Pro-I"
        ],
        "Asus": [
                "ROG Phone 9 Pro",
                "ROG Phone 9",
                "ROG Phone 8 Pro",
                "ROG Phone 8",
                "ROG Phone 7 Ultimate",
                "ROG Phone 7",
                "ROG Phone 6",
                "Zenfone 12 Ultra",
                "Zenfone 11 Ultra",
                "Zenfone 10",
                "Zenfone 9",
                "Zenfone 8"
        ]
    },
    "game_console": {
        "Sony PlayStation": [
                "PlayStation 5 Pro",
                "PlayStation 5 Slim",
                "PlayStation 5 Digital Edition",
                "PlayStation 5 (original)",
                "PlayStation Portal",
                "PlayStation 4 Pro",
                "PlayStation 4 Slim",
                "PlayStation 4"
        ],
        "Microsoft Xbox": [
                "Xbox Series X",
                "Xbox Series S",
                "Xbox One X",
                "Xbox One S",
                "Xbox One",
                "Xbox 360"
        ],
        "Nintendo": [
                "Switch 2",
                "Switch OLED",
                "Switch (standard)",
                "Switch Lite",
                "Wii U",
                "3DS"
        ],
        "Valve Steam Deck": [
                "Steam Deck OLED",
                "Steam Deck LCD"
        ],
        "Asus ROG Ally": [
                "ROG Xbox Ally X",
                "ROG Xbox Ally",
                "ROG Ally X",
                "ROG Ally"
        ],
        "Meta Quest": [
                "Quest 3S",
                "Quest 3",
                "Quest Pro",
                "Quest 2"
        ]
    },
}

from models_data import MORE_MODELS  # noqa: E402

MODELS_BY_BRAND.update(MORE_MODELS)

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
