"""Small shared formatting helpers."""

from __future__ import annotations

import html
from datetime import datetime, timezone


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def local_datetime(value: str | None) -> datetime | None:
    parsed = parse_timestamp(value)
    return parsed.astimezone() if parsed else None


def format_timestamp(value: str | None, with_time: bool = True) -> str:
    parsed = local_datetime(value)
    if not parsed:
        return "Unknown date"
    return parsed.strftime("%b %d, %Y · %H:%M" if with_time else "%b %d, %Y")


def format_short_timestamp(value: str | None) -> str:
    parsed = local_datetime(value)
    return parsed.strftime("%b %d · %H:%M") if parsed else "—"


def relative_time(value: str | None) -> str:
    parsed = local_datetime(value)
    if not parsed:
        return "Unknown"

    now = datetime.now(timezone.utc).astimezone()
    seconds = max(0, int((now - parsed).total_seconds()))
    if seconds < 60:
        return "Just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago"
    days = hours // 24
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    return parsed.strftime("%b %d, %Y")


def day_label(value: str | None) -> str:
    parsed = local_datetime(value)
    if not parsed:
        return "Unknown date"
    today = datetime.now(timezone.utc).astimezone().date()
    if parsed.date() == today:
        return f"Today · {parsed.strftime('%H:%M')}"
    delta = (today - parsed.date()).days
    if delta == 1:
        return f"Yesterday · {parsed.strftime('%H:%M')}"
    return parsed.strftime("%b %d, %Y · %H:%M")


def escape(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def nl2br(value: object) -> str:
    return escape(value).replace("\n", "<br>")


def truncate(value: str, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: max(1, limit - 1)].rstrip() + "…"


def title_case(value: str) -> str:
    return str(value or "").replace("_", " ").strip().title()


def severity_tone(value: str) -> str:
    severity = str(value or "").lower()
    if severity in {"critical", "severe", "urgent"}:
        return "critical"
    if severity in {"high", "soon"}:
        return "high"
    if severity in {"moderate", "medium"}:
        return "moderate"
    if severity in {"low", "routine", "none", "minor"}:
        return "low"
    return "neutral"


def device_string(manufacturer: str = "", model: str = "") -> str:
    combined = " ".join(part.strip() for part in (manufacturer, model) if part and part.strip())
    return combined or "Unspecified device"
