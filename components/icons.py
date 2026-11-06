"""Inline SVG icon library and brand lockup."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

_ICONS: dict[str, str] = {
    "smartphone": """
        <rect x="7" y="2.5" width="10" height="19" rx="2.6"/>
        <path d="M10.5 5.5h3"/><circle cx="12" cy="18.2" r=".6" fill="currentColor" stroke="none"/>
    """,
    "laptop": """
        <rect x="4" y="4.5" width="16" height="11" rx="1.8"/>
        <path d="M2 18.5h20M9.5 18.5h5"/>
    """,
    "desktop": """
        <rect x="3" y="4" width="13.5" height="10" rx="1.8"/>
        <path d="M6.5 18.5h8M9.5 14v4.5M20.5 7v10.5M19 17.5h3M19 20h3"/>
    """,
    "washer": """
        <rect x="4.5" y="2.8" width="15" height="18.4" rx="2.6"/>
        <circle cx="12" cy="13" r="4.2"/>
        <path d="M7.5 6.5h.01M10.5 6.5h.01M16.5 18.8c-1.6-1-1.2-2.5.2-3.1"/>
    """,
    "refrigerator": """
        <rect x="5.5" y="2.5" width="13" height="19" rx="2.2"/>
        <path d="M5.5 9.8h13M8.5 5.5v2M8.5 12.5v2.5"/>
    """,
    "air_conditioner": """
        <rect x="2.5" y="5" width="19" height="8.5" rx="2.4"/>
        <path d="M5.5 10.8h13M8 16.2c0 1.7-1 2.2-1 3.3M12 16.2c0 2-1.2 2.5-1.2 3.8M16 16.2c0 1.7-1 2.2-1 3.3"/>
    """,
    "television": """
        <rect x="2.5" y="4" width="19" height="12.5" rx="2.2"/>
        <path d="M8 20.5h8M12 16.5v4"/>
    """,
    "tablet": """
        <rect x="4" y="3" width="16" height="18" rx="2.4"/><path d="M10.5 18.2h3"/>
    """,
    "printer": """
        <path d="M7 8V3.5h10V8"/><rect x="3.5" y="8" width="17" height="8.5" rx="2"/><rect x="7" y="13" width="10" height="7.5" rx="1"/>
    """,
    "game_console": """
        <path d="M7.5 7h9a4.5 4.5 0 0 1 4.4 5.4l-.7 3.4a2.4 2.4 0 0 1-4 1.3L14 15.5h-4l-2.2 2.1a2.4 2.4 0 0 1-4-1.3l-.7-3.4A4.5 4.5 0 0 1 7.5 7Z"/>
        <path d="M8 10v3M6.5 11.5h3M15.5 10.6h.01M17.5 12.4h.01"/>
    """,
    "router": """
        <rect x="3" y="13" width="18" height="6.5" rx="2"/><path d="M7 16.2h.01M10.5 16.2h.01M9 10.5a4.2 4.2 0 0 1 6 0M6.2 7.6a8.2 8.2 0 0 1 11.6 0"/>
    """,
    "microwave": """
        <rect x="2.5" y="5" width="19" height="14" rx="2.4"/><rect x="5.5" y="8" width="9" height="8" rx="1.2"/><path d="M17.5 8.5h1M17.5 12h1M17.5 15.5h1"/>
    """,
    "dishwasher": """
        <rect x="4.5" y="2.8" width="15" height="18.4" rx="2.4"/><path d="M4.5 8h15M7.5 5.4h.01M10.5 5.4h.01"/><circle cx="12" cy="14.3" r="3.4"/>
    """,
    "smartwatch": """
        <rect x="7" y="6.5" width="10" height="11" rx="3"/><path d="m9 6.5.8-3.5h4.4l.8 3.5M9 17.5l.8 3.5h4.4l.8-3.5M12 10v2.2l1.4 1"/>
    """,
    "headphones": """
        <path d="M4 15v-3a8 8 0 0 1 16 0v3"/><rect x="3.5" y="14" width="4" height="6" rx="1.6"/><rect x="16.5" y="14" width="4" height="6" rx="1.6"/>
    """,
    "plug": """
        <path d="M8.5 3v5M15.5 3v5M6 8h12v3.5a6 6 0 0 1-6 6v0a6 6 0 0 1-6-6V8ZM12 17.5V21"/>
    """,
    "chip": """
        <rect x="6" y="6" width="12" height="12" rx="2"/>
        <rect x="9.5" y="9.5" width="5" height="5" rx="1"/>
        <path d="M9 2.5V6M15 2.5V6M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5"/>
    """,
    "sparkles": """
        <path d="M12 2.8 13.7 8l5.2 1.7-5.2 1.7L12 16.6l-1.7-5.2L5.1 9.7 10.3 8 12 2.8Z"/>
        <path d="M19 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2ZM5 16l.6 1.6 1.6.6-1.6.6L5 20.4l-.6-1.6L2.8 18l1.6-.6L5 16Z"/>
    """,
    "eye": """
        <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/>
        <circle cx="12" cy="12" r="3"/>
    """,
    "scan": """
        <path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/>
        <path d="M3 12h18"/>
    """,
    "shield": """
        <path d="M12 2.8 20 6v5.3c0 5-3.4 8.5-8 9.9-4.6-1.4-8-4.9-8-9.9V6l8-3.2Z"/>
        <path d="m8.6 12 2.3 2.3 4.5-4.6"/>
    """,
    "chat": """
        <path d="M20.8 11.7a8.2 8.2 0 0 1-8.2 8.2 8.7 8.7 0 0 1-3.2-.6L4 21l1.4-4.2a8.2 8.2 0 1 1 15.4-5.1Z"/>
        <path d="M8.5 11.5h.01M12 11.5h.01M15.5 11.5h.01"/>
    """,
    "database": """
        <ellipse cx="12" cy="5" rx="8" ry="3"/>
        <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/>
    """,
    "history": """
        <path d="M3 12a9 9 0 1 0 2.6-6.4L3 8.2"/>
        <path d="M3 3.5v4.7h4.7M12 7.5V12l3 2"/>
    """,
    "gauge": """
        <path d="M4.1 18a9 9 0 1 1 15.8 0"/>
        <path d="m12 13 3.8-3.8"/>
        <circle cx="12" cy="13" r="1.6"/>
    """,
    "wrench": """
        <path d="M14.6 6.2a4.2 4.2 0 0 0-5.4 5.4L3.6 17.2a2 2 0 0 0 2.8 2.8l5.6-5.6a4.2 4.2 0 0 0 5.4-5.4l-2.6 2.6-2.8-2.8 2.6-2.6Z"/>
    """,
    "clock": """
        <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/>
    """,
    "alert": """
        <path d="M10.3 3.6 2.2 17.7A2 2 0 0 0 3.9 20.7h16.2a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z"/>
        <path d="M12 9v4.5M12 17h.01"/>
    """,
    "check": """<path d="m4.5 12.5 4.7 4.7L19.7 6.7"/>""",
    "check-circle": """
        <circle cx="12" cy="12" r="9"/><path d="m8 12.2 2.7 2.7 5.4-5.6"/>
    """,
    "x": """<path d="M6 6l12 12M18 6 6 18"/>""",
    "search": """<circle cx="11" cy="11" r="7"/><path d="m16.2 16.2 4.3 4.3"/>""",
    "trash": """
        <path d="M4 6.5h16M9 6.5V3.8h6v2.7M6 6.5l.9 13a2 2 0 0 0 2 1.9h6.2a2 2 0 0 0 2-1.9l.9-13"/>
        <path d="M10 10.5v6M14 10.5v6"/>
    """,
    "plus": """<path d="M12 4.5v15M4.5 12h15"/>""",
    "arrow-right": """<path d="M4.5 12h15M13 5.5l6.5 6.5L13 18.5"/>""",
    "arrow-up-right": """<path d="M7 17 17 7M8 7h9v9"/>""",
    "chevron-down": """<path d="m6 9 6 6 6-6"/>""",
    "refresh": """
        <path d="M20 7.5v5h-5M4 16.5v-5h5"/>
        <path d="M6.1 8.3A7.5 7.5 0 0 1 19.9 12M4.1 12a7.5 7.5 0 0 0 13.8 3.7"/>
    """,
    "image": """
        <rect x="3" y="3" width="18" height="18" rx="3"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <path d="m3.5 17 5-5 4.3 4.3 2.7-2.7 5 5"/>
    """,
    "lock": """
        <rect x="4.5" y="10" width="15" height="10.5" rx="2.5"/>
        <path d="M8 10V7.5a4 4 0 0 1 8 0V10M12 14v2.5"/>
    """,
    "layers": """
        <path d="m12 2.8 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16.2l9 5 9-5"/>
    """,
    "target": """
        <circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>
    """,
    "activity": """<path d="M3 12h4.2l2.1-6.2 4 12.4 2.4-6.2H21"/>""",
    "bolt": """<path d="M13.2 2.5 4.8 13.4h6.1L10 21.5l8.6-11.2h-6.2l.8-7.8Z"/>""",
    "home": """
        <path d="m3 10.5 9-7.2 9 7.2V20a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 20v-9.5Z"/>
        <path d="M9 21.5v-7h6v7"/>
    """,
    "grid": """
        <rect x="3" y="3" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/>
        <rect x="3" y="13.5" width="7.5" height="7.5" rx="2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/>
    """,
    "send": """<path d="M21 3 10.5 13.5M21 3l-6.7 18-3.8-7.5L3 9.7 21 3Z"/>""",
    "tune": """
        <path d="M4 7h7M15 7h5M4 17h3M11 17h9M4 12h11M19 12h1"/>
        <circle cx="13" cy="7" r="2"/><circle cx="9" cy="17" r="2"/><circle cx="17" cy="12" r="2"/>
    """,
    "info": """<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/>""",
    "thermometer": """
        <path d="M10 14.2V5a2 2 0 1 1 4 0v9.2a4.2 4.2 0 1 1-4 0Z"/><path d="M12 9v6"/>
    """,
    "cpu": """
        <rect x="6" y="6" width="12" height="12" rx="2.5"/>
        <path d="M9.5 9.5h5v5h-5zM9 2.5V6M15 2.5V6M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5"/>
    """,
}

_LOGO_PULSE = """
    <path d="M3.5 12.2h4.1l1.9-5.1 3.5 9.8 2.2-4.7h5.3" />
    <circle cx="20.5" cy="12.2" r="1.35" fill="currentColor" stroke="none"/>
"""


def icon(name: str, size: int = 22, class_name: str = "") -> str:
    inner = _ICONS.get(name, _ICONS["chip"])
    classes = f"fm-svg {class_name}".strip()
    return (
        f'<svg class="{classes}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" focusable="false">{inner}</svg>'
    )


@lru_cache(maxsize=1)
def _logo_data_uri() -> str:
    path = Path(__file__).resolve().parent.parent / "assets" / "logo_mark.png"
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def logo_mark(size: int = 38) -> str:
    return (
        f'<img src="{_logo_data_uri()}" alt="FixMate logo" width="{size}" height="{size}" '
        f'style="display:block;width:{size}px;height:{size}px;border-radius:22%;'
        f'box-shadow:0 0 0 1.5px rgba(255,255,255,.75)">'
    )


def brand_lockup(size: int = 38, subtle: bool = False) -> str:
    tone = " fm-brand-subtle" if subtle else ""
    return (
        f'<div class="fm-brand{tone}">{logo_mark(size)}'
        f'<div class="fm-brand-word"><span>FixMate</span><em>AI</em></div></div>'
    )
