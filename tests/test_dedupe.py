from app.dedupe import is_duplicate, make_content_hash
from app.models import Lead


def test_duplicate_by_url(session):
    session.add(
        Lead(
            source="Test",
            source_type="api",
            source_url="https://x.test/a",
            title="Event Photographer",
            company="ABC",
            location="London",
            category="event",
            role_type="unknown",
            media_type="photo",
            relevance_score=80,
            confidence_score=0.9,
            status="new",
            content_hash=make_content_hash("Event Photographer", "desc", "ABC", "London"),
        )
    )
    session.flush()
    payload = {
        "source_url": "https://x.test/a",
        "title": "Another title",
        "company": "DEF",
        "location": "Leeds",
        "description": "text",
        "content_hash": make_content_hash("Another title", "text", "DEF", "Leeds"),
    }
    assert is_duplicate(session, payload)
