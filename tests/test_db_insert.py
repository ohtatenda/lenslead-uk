from app.dedupe import make_content_hash
from app.models import Lead


def test_database_insert(session):
    lead = Lead(
        source="manual",
        source_type="manual",
        source_url=None,
        title="Freelance Videographer",
        company="Studio One",
        location="Manchester",
        category="general",
        role_type="freelance_project",
        media_type="video",
        relevance_score=70,
        confidence_score=0.8,
        status="new",
        content_hash=make_content_hash("Freelance Videographer", "desc", "Studio One", "Manchester"),
    )
    session.add(lead)
    session.flush()
    assert lead.id is not None
    assert lead.created_at is not None
