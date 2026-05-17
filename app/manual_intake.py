from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.classify import classify_lead
from app.dedupe import is_duplicate, make_content_hash
from app.models import Lead, ManualInput
from app.scoring import score_lead


def parse_manual_text(raw_text: str) -> dict:
    text = raw_text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0][:280] if lines else "Manual opportunity"
    location_match = re.search(
        r"\b(london|ilford|essex|kent|surrey|hertfordshire|birmingham|manchester|bristol|leeds|brighton|cambridge|oxford|uk|remote|hybrid)\b",
        text,
        re.IGNORECASE,
    )
    pay_match = re.search(r"(£\s?\d[\d,]*(?:\s?-\s?£?\d[\d,]*)?(?:\s?(?:per day|per hour|day|hour))?)", text, re.IGNORECASE)
    email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
    phone_match = re.search(r"(\+?\d[\d\s\-]{8,}\d)", text)
    date_match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)

    return {
        "title": title,
        "location": location_match.group(0).title() if location_match else "",
        "pay_text": pay_match.group(0) if pay_match else "",
        "contact_email": email_match.group(1) if email_match else "",
        "contact_phone": phone_match.group(1) if phone_match else "",
        "date_of_event": date_match.group(1) if date_match else "",
        "description": text[:4000],
        "posted_date": datetime.utcnow().date().isoformat(),
    }


def save_manual_input(session: Session, raw_text: str) -> Lead | None:
    parsed = parse_manual_text(raw_text)
    classification = classify_lead(parsed["title"], parsed["description"])
    score = score_lead(parsed["title"], parsed["description"], classification.category, parsed["location"], parsed["pay_text"])
    payload = {
        **parsed,
        "source": "manual",
        "source_type": "manual",
        "source_url": None,
        "company": "",
        "remote_type": "unknown",
        "category": classification.category,
        "sub_category": "",
        "role_type": classification.role_type,
        "media_type": classification.media_type,
        "job_type": "freelance",
        "pay_min": None,
        "pay_max": None,
        "currency": "GBP",
        "deadline": None,
        "contact_name": None,
        "apply_url": None,
        "relevance_score": float(score.score),
        "confidence_score": classification.confidence,
        "status": "new",
        "notes": "",
        "content_hash": make_content_hash(parsed["title"], parsed["description"], "", parsed["location"]),
        "score_reasons": "; ".join(score.reasons),
        "red_flags": "; ".join(score.red_flags),
    }
    if is_duplicate(session, payload):
        return None
    lead = Lead(**payload)
    session.add(ManualInput(raw_text=raw_text, parsed_summary=str(parsed)))
    session.add(lead)
    session.flush()
    return lead
