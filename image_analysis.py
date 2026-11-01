"""Image ingestion and AI-assisted visual inspection."""

from __future__ import annotations

import io
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from PIL import Image, ImageOps, UnidentifiedImageError

from ai_service import AIError, analyze_images
from config import get_ai_settings
from diagnostic_engine import build_image_context, normalise_image_analysis

Image.MAX_IMAGE_PIXELS = 32_000_000
MAX_FILES = 4
MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


class ImageValidationError(ValueError):
    """A user-correctable problem with an uploaded image."""


@dataclass
class PreparedImage:
    name: str
    mime_type: str
    data: bytes
    width: int
    height: int
    original_kb: int
    prepared_kb: int


def prepare_image(uploaded_file) -> PreparedImage:
    if uploaded_file is None:
        raise ImageValidationError("No file was provided.")

    raw = uploaded_file.getvalue()
    if not raw:
        raise ImageValidationError(f"{uploaded_file.name} is empty.")
    if len(raw) > MAX_FILE_BYTES:
        raise ImageValidationError(f"{uploaded_file.name} is larger than 10 MB. Please use a smaller photo.")

    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in ALLOWED_FORMATS:
                raise ImageValidationError(
                    f"{uploaded_file.name} is a {source.format or 'unknown'} file. Use JPG, PNG, or WebP."
                )
            width, height = source.size
            if width < 48 or height < 48:
                raise ImageValidationError(f"{uploaded_file.name} is too small to inspect. Use a clear photo.")
            if width * height > 32_000_000:
                raise ImageValidationError(f"{uploaded_file.name} has extremely large dimensions. Please resize it.")

            source = ImageOps.exif_transpose(source)
            if source.mode in {"RGBA", "LA", "P"}:
                source = source.convert("RGBA")
                background = Image.new("RGB", source.size, (245, 247, 250))
                background.paste(source, mask=source.getchannel("A"))
                image = background
            else:
                image = source.convert("RGB")

            max_edge = 1400
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(output, format="JPEG", quality=88, optimize=True)
            prepared = output.getvalue()
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise ImageValidationError(
            f"{uploaded_file.name} could not be read as an image. Try exporting it as a JPG or PNG."
        ) from None

    return PreparedImage(
        name=uploaded_file.name,
        mime_type="image/jpeg",
        data=prepared,
        width=image.width,
        height=image.height,
        original_kb=max(1, len(raw) // 1024),
        prepared_kb=max(1, len(prepared) // 1024),
    )


def prepare_uploads(uploaded_files) -> tuple[list[PreparedImage], list[str]]:
    prepared: list[PreparedImage] = []
    errors: list[str] = []
    files = list(uploaded_files or [])[:MAX_FILES]
    for uploaded_file in files:
        try:
            prepared.append(prepare_image(uploaded_file))
        except ImageValidationError as exc:
            errors.append(str(exc))
    return prepared, errors


def run_image_analysis(images: list[PreparedImage], diagnostic: dict) -> dict:
    if not images:
        raise AIError("Add at least one photo before running a visual inspection.", kind="invalid_image")

    started = time.perf_counter()
    context = build_image_context(diagnostic)
    raw = analyze_images([(image.data, image.mime_type) for image in images], context)
    analysis = normalise_image_analysis(raw)

    hazard_levels = {str(item.get("level", "")).lower() for item in diagnostic.get("hazards", [])}
    if hazard_levels & {"critical", "high"}:
        review = analysis["professional_review"]
        review["recommended"] = True
        if review.get("urgency") == "routine":
            review["urgency"] = "soon"
        if not review.get("reason"):
            review["reason"] = "A safety hazard was already flagged for this device; visual confirmation supports professional review."

    settings = get_ai_settings()
    analysis["_meta"] = {
        "model": settings.vision_model,
        "analyzed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "image_count": len(images),
        "duration_seconds": round(time.perf_counter() - started, 2),
    }
    return analysis
