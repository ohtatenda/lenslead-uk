from __future__ import annotations

from typing import Any

from app.classify import classify_lead
from app.dedupe import make_content_hash
from app.scoring import score_lead


def normalize_lead(source: str, source_type: str, item: dict[str, Any]) -> dict[str, Any]:
    title = item.get("title", "").strip() or "Untitled opportunity"
    description = (item.get("description") or "").strip()
    location = (item.get("location") or "").strip()
    classification = classify_lead(title, description)
    score = score_lead(title, description, classification.category, location, item.get("pay_text", "") or "")
    return {
        "source": source,
        "source_type": source_type,
        "source_url": item.get("source_url"),
        "title": title[:300],
        "company": (item.get("company") or "")[:200],
        "location": location[:200],
        "remote_type": item.get("remote_type") or "unknown",
        "category": item.get("category") or classification.category,
        "sub_category": item.get("sub_category"),
        "role_type": item.get("role_type") or classification.role_type,
        "media_type": item.get("media_type") or classification.media_type,
        "job_type": item.get("job_type") or "unknown",
        "pay_text": item.get("pay_text"),
        "pay_min": item.get("pay_min"),
        "pay_max": item.get("pay_max"),
        "currency": item.get("currency") or "GBP",
        "date_of_event": item.get("date_of_event"),
        "posted_date": item.get("posted_date"),
        "deadline": item.get("deadline"),
        "description": description[:8000],
        "contact_name": item.get("contact_name"),
        "contact_email": item.get("contact_email"),
        "contact_phone": item.get("contact_phone"),
        "apply_url": item.get("apply_url") or item.get("source_url"),
        "relevance_score": float(score.score),
        "confidence_score": float(item.get("confidence_score", classification.confidence)),
        "status": item.get("status") or "new",
        "notes": item.get("notes"),
        "content_hash": make_content_hash(title, description, item.get("company", ""), location),
        "score_reasons": "; ".join(score.reasons),
        "red_flags": "; ".join(score.red_flags),
    }
