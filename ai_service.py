"""OpenAI client integration for diagnosis, vision analysis, and chat.

Every failure path raises an AIError with a human-readable message. The app
never substitutes a fabricated result when a real API call fails.
"""

from __future__ import annotations

import base64
import json
from typing import Iterable

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from config import AISettings, get_ai_settings
from i18n import language_name
from prompts import CHAT_SYSTEM_PROMPT, DIAGNOSIS_SYSTEM_PROMPT, VISION_SYSTEM_PROMPT


class AIError(RuntimeError):
    """A failure that can be shown to the user without leaking secrets."""

    def __init__(self, message: str, kind: str = "unknown", detail: str = ""):
        super().__init__(message)
        self.message = message
        self.kind = kind
        self.detail = detail


MISSING_KEY_MESSAGE = (
    "FixMate AI needs an OpenAI API key before it can run a live analysis.\n\n"
    "Local setup: add OPENAI_API_KEY to the `.env` file in the project folder and restart the app.\n"
    "Streamlit Community Cloud: add OPENAI_API_KEY under App settings → Secrets.\n\n"
    "No key is included with this project. All AI features remain offline until a valid key is configured."
)


def _get_client(settings: AISettings) -> OpenAI:
    if not settings.configured:
        raise AIError(MISSING_KEY_MESSAGE, kind="missing_key")

    kwargs = {
        "api_key": settings.api_key,
        "timeout": settings.timeout_seconds,
        "max_retries": 1,
    }
    if settings.base_url:
        kwargs["base_url"] = settings.base_url
    return OpenAI(**kwargs)


def _safe_detail(exc: Exception, settings: AISettings) -> str:
    """Short provider message for troubleshooting, with the API key removed."""
    text = " ".join(str(exc).split())
    if settings.api_key:
        text = text.replace(settings.api_key, "[hidden]")
    return text[:350]


def _map_error(exc: Exception, settings: AISettings) -> AIError:
    """Translate SDK exceptions into useful, non-secret error messages."""
    if isinstance(exc, AIError):
        return exc
    if isinstance(exc, AuthenticationError):
        return AIError(
            "The OpenAI API rejected the configured key. Check that OPENAI_API_KEY is current and has access "
            "to the selected model.",
            kind="auth",
        )
    if isinstance(exc, RateLimitError):
        return AIError(
            "The AI service is rate-limited or the account has reached its usage limit. Wait a moment and retry, "
            "or check your OpenAI usage settings.",
            kind="rate_limit",
        )
    if isinstance(exc, APITimeoutError):
        return AIError(
            "The AI request timed out. Check your connection and try again. Vision requests with several images "
            "can take longer.",
            kind="timeout",
        )
    if isinstance(exc, APIConnectionError):
        return AIError(
            "FixMate could not reach the AI service. Check your internet connection or OPENAI_BASE_URL, then retry.",
            kind="connection",
        )
    if isinstance(exc, BadRequestError):
        message = str(exc)
        if "model" in message.lower() and ("not found" in message.lower() or "does not exist" in message.lower()):
            return AIError(
                f"The configured model `{settings.model}` is not available to this API key. "
                "Change OPENAI_MODEL or OPENAI_VISION_MODEL in your settings.",
                kind="model",
            )
        if "image" in message.lower():
            return AIError(
                "The AI service rejected one of the images. Try a smaller JPG or PNG image and submit again.",
                kind="invalid_image",
            )
        return AIError(
            "The AI service rejected the request. Check the configured model and image settings, then try again. "
            f"Details: {_safe_detail(exc, settings)}",
            kind="bad_request",
        )
    if isinstance(exc, APIStatusError):
        return AIError(
            f"The AI service returned an error (code {getattr(exc, 'status_code', '?')}). "
            f"Details: {_safe_detail(exc, settings)}",
            kind="service",
        )
    if isinstance(exc, OpenAIError):
        return AIError(
            "The AI request could not be completed. Please retry. If the problem continues, verify your API "
            "configuration.",
            kind="service",
        )
    return AIError(
        "An unexpected error interrupted the AI request. No diagnosis was generated. Please retry.",
        kind="unexpected",
        detail=type(exc).__name__,
    )


def _extract_text(completion) -> str:
    if not completion.choices:
        raise AIError("The AI service returned an empty response. Please retry.", kind="empty")

    choice = completion.choices[0]
    if getattr(choice, "finish_reason", None) == "length":
        raise AIError(
            "The AI response was cut off before it could complete. Please retry; if it keeps happening, reduce the "
            "amount of text in your description.",
            kind="truncated",
        )
    if getattr(choice, "finish_reason", None) == "content_filter":
        raise AIError(
            "The AI service filtered this response. Rephrase the description using neutral, factual language.",
            kind="filtered",
        )
    message = choice.message
    content = getattr(message, "content", None)
    if not content or not str(content).strip():
        raise AIError("The AI service returned an empty response. Please retry.", kind="empty")
    return str(content)


def _parse_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            if first_line.strip().lower() in {"json", "javascript"}:
                text = rest
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise AIError(
                "The AI returned a response FixMate could not read. No report was created. Please retry.",
                kind="invalid_json",
            ) from None
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            raise AIError(
                "The AI returned an incomplete structured response. No report was created. Please retry.",
                kind="invalid_json",
            ) from None

    if not isinstance(payload, dict):
        raise AIError(
            "The AI returned an unexpected response format. No report was created. Please retry.",
            kind="invalid_json",
        )
    return payload


_TRANSLATE_PROMPT = """You translate text for FixMate AI, a consumer repair-triage app, into {language}.
The input is a JSON array of strings. Return ONLY a JSON object {{"translations": [...]}} with exactly the same
number of items in the same order. Translate faithfully, plainly and calmly. Keep brand names, model names, error codes,
numbers and units unchanged. Never add, merge, drop or explain items."""


def translate_texts(texts: list[str], language: str, settings: AISettings | None = None) -> list[str]:
    """Translate report text after the safety layer has already checked the English version."""
    settings = settings or get_ai_settings()
    client = _get_client(settings)
    try:
        completion = client.chat.completions.create(
            model=settings.model,
            messages=[
                {"role": "system", "content": _TRANSLATE_PROMPT.format(language=language)},
                {"role": "user", "content": json.dumps(texts, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=settings.diagnosis_tokens,
        )
    except OpenAIError as exc:
        raise _map_error(exc, settings) from exc
    items = _parse_json_object(_extract_text(completion)).get("translations")
    if not isinstance(items, list) or len(items) != len(texts) or not all(isinstance(i, str) for i in items):
        raise AIError("The translation was incomplete.", kind="invalid_report")
    return items


def _language_note() -> str:
    name = language_name()
    if not name:
        return ""
    return f"\n\nLANGUAGE\nWrite your whole reply in {name}. Keep brand names, model names and error codes as written."


def generate_diagnosis(user_context: str, settings: AISettings | None = None) -> dict:
    settings = settings or get_ai_settings()
    client = _get_client(settings)
    try:
        completion = client.chat.completions.create(
            model=settings.model,
            messages=[
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_context},
            ],
            response_format={"type": "json_object"},
            temperature=0.25,
            max_tokens=settings.diagnosis_tokens,
        )
    except Exception as exc:
        raise _map_error(exc, settings) from exc

    content = _extract_text(completion)
    return _parse_json_object(content)


def analyze_images(
    images: Iterable[tuple[bytes, str]],
    user_context: str,
    settings: AISettings | None = None,
) -> dict:
    settings = settings or get_ai_settings()
    client = _get_client(settings)
    images = list(images)
    if not images:
        raise AIError("No images were supplied for analysis.", kind="invalid_image")

    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "Inspect the supplied photographs for this repair case. Only describe visible evidence.\n\n"
                f"{user_context}"
            ),
        }
    ]
    for image_bytes, mime_type in images:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{encoded}", "detail": "high"},
            }
        )

    try:
        completion = client.chat.completions.create(
            model=settings.vision_model,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=settings.vision_tokens,
        )
    except Exception as exc:
        raise _map_error(exc, settings) from exc

    response = _extract_text(completion)
    return _parse_json_object(response)


def chat_reply(
    conversation: list[dict],
    context_text: str,
    settings: AISettings | None = None,
) -> str:
    settings = settings or get_ai_settings()
    client = _get_client(settings)
    trimmed = conversation[-20:]
    messages = [
        {
            "role": "system",
            "content": f"{CHAT_SYSTEM_PROMPT}\n\nCURRENT DIAGNOSTIC CONTEXT\n{context_text}{_language_note()}",
        },
        *[
            {"role": item["role"], "content": item["content"]}
            for item in trimmed
            if item.get("role") in {"user", "assistant"} and item.get("content")
        ],
    ]

    try:
        completion = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            temperature=0.4,
            max_tokens=settings.chat_tokens,
        )
    except Exception as exc:
        raise _map_error(exc, settings) from exc

    return _extract_text(completion).strip()
