from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return re.sub(r"[^a-z0-9 ]", "", value)


def make_content_hash(title: str, description: str, company: str = "", location: str = "") -> str:
    raw = f"{normalize_text(title)}|{normalize_text(company)}|{normalize_text(location)}|{normalize_text(description)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_duplicate(session: Session, lead_payload: dict) -> bool:
    source_url = lead_payload.get("source_url")
    if source_url:
        existing_by_url = session.scalar(select(Lead).where(Lead.source_url == source_url))
        if existing_by_url:
            return True

    content_hash = lead_payload.get("content_hash")
    if content_hash:
        existing_by_hash = session.scalar(select(Lead).where(Lead.content_hash == content_hash))
        if existing_by_hash:
            return True

    title = normalize_text(lead_payload.get("title"))
    company = normalize_text(lead_payload.get("company"))
    location = normalize_text(lead_payload.get("location"))
    if title:
        existing_similar = session.scalars(select(Lead).where(Lead.title.ilike(f"%{lead_payload.get('title', '')}%"))).all()
        for candidate in existing_similar:
            candidate_key = f"{normalize_text(candidate.title)}|{normalize_text(candidate.company)}|{normalize_text(candidate.location)}"
            key = f"{title}|{company}|{location}"
            if candidate_key == key:
                return True
            sim = SequenceMatcher(
                None,
                normalize_text(candidate.title + " " + (candidate.description or "")),
                normalize_text(lead_payload.get("title", "") + " " + lead_payload.get("description", "")),
            ).ratio()
            if sim >= 0.94:
                return True
    return False
