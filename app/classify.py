from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class ClassificationResult:
    category: str
    media_type: str
    role_type: str
    confidence: float


WEDDING_TERMS = {"wedding", "bridal", "second shooter"}
EVENT_TERMS = {"event", "conference", "festival", "corporate event", "red carpet"}
IRRELEVANT_TERMS = {"radiographer", "retail assistant", "art teacher", "school teacher"}


def _contains_any(text: str, words: set[str]) -> bool:
    lower = text.lower()
    return any(w in lower for w in words)


def classify_lead(title: str, description: str = "") -> ClassificationResult:
    blob = f"{title} {description}".lower()
    if _contains_any(blob, IRRELEVANT_TERMS):
        return ClassificationResult("irrelevant", "unknown", "unknown", 0.95)

    if _contains_any(blob, WEDDING_TERMS):
        category = "wedding"
    elif _contains_any(blob, EVENT_TERMS):
        category = "event"
    elif re.search(r"\b(photo|video|photographer|videographer|editor|content)\b", blob):
        category = "general"
    else:
        category = "needs_review"

    if "photographer" in blob and "videographer" in blob:
        media_type = "photo_video"
    elif "videographer" in blob or "video" in blob or "filmmaker" in blob:
        media_type = "video"
    elif "editor" in blob:
        media_type = "editing"
    elif "content creator" in blob:
        media_type = "content_creation"
    elif "photographer" in blob or "photo" in blob:
        media_type = "photo"
    else:
        media_type = "unknown"

    role_type = "unknown"
    for term, mapped in [
        ("second shooter", "second_shooter"),
        ("associate", "associate"),
        ("assistant", "assistant"),
        ("editor", "editor"),
        ("content creator", "content_creator"),
        ("camera operator", "camera_operator"),
        ("studio", "studio_role"),
        ("freelance", "freelance_project"),
        ("full time", "full_time_job"),
        ("lead photographer", "lead_shooter"),
    ]:
        if term in blob:
            role_type = mapped
            break
    confidence = 0.85 if category != "needs_review" else 0.55
    result = ClassificationResult(category, media_type, role_type, confidence)
    return maybe_openai_refine(title, description, result)


def maybe_openai_refine(title: str, description: str, baseline: ClassificationResult) -> ClassificationResult:
    settings = get_settings()
    if not settings.openai_api_key:
        return baseline
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            "Classify this UK lead into category (wedding/event/general/irrelevant/needs_review), "
            "media_type (photo/video/photo_video/editing/content_creation/unknown), and role_type "
            "(lead_shooter/second_shooter/associate/assistant/editor/content_creator/camera_operator/studio_role/freelance_project/full_time_job/unknown). "
            "Return CSV line only.\n"
            f"Title: {title}\nDescription: {description[:1000]}"
        )
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
        text = response.output_text.strip().splitlines()[0]
        parts = [p.strip().lower() for p in text.split(",")]
        if len(parts) >= 3:
            return ClassificationResult(parts[0], parts[1], parts[2], 0.9)
    except Exception:
        return baseline
    return baseline
