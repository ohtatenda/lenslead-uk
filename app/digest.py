from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead, Run


def _top_leads(session: Session, category: str, limit: int = 10) -> list[Lead]:
    return session.scalars(
        select(Lead)
        .where(Lead.category == category)
        .order_by(Lead.relevance_score.desc(), Lead.created_at.desc())
        .limit(limit)
    ).all()


def _format_leads(leads: list[Lead]) -> str:
    if not leads:
        return "- No leads found.\n"
    output = []
    for lead in leads:
        output.append(
            f"- **{lead.title}** ({lead.location or 'Unknown'}) — score {int(lead.relevance_score)} — [source]({lead.source_url or lead.apply_url or '#'})"
        )
    return "\n".join(output) + "\n"


def generate_daily_digest(session: Session) -> str:
    last_run = session.scalar(select(Run).order_by(Run.started_at.desc()))
    since = last_run.started_at if last_run else datetime.min
    new_leads = session.scalars(select(Lead).where(Lead.created_at >= since)).all()
    high_priority = session.scalars(select(Lead).where(Lead.relevance_score >= 75).order_by(Lead.relevance_score.desc())).all()
    needs_review = session.scalars(select(Lead).where(Lead.category == "needs_review")).all()

    md = [
        "# LensLead UK Daily Digest",
        f"_Generated: {datetime.utcnow().isoformat()} UTC_",
        "",
        "## Top 10 Wedding Leads",
        _format_leads(_top_leads(session, "wedding")),
        "## Top 10 Event Leads",
        _format_leads(_top_leads(session, "event")),
        "## Top 10 General Leads",
        _format_leads(_top_leads(session, "general")),
        "## Newly Found Since Last Run",
        _format_leads(new_leads[:20]),
        "## High Priority (Score > 75)",
        _format_leads(high_priority[:20]),
        "## Needs Review",
        _format_leads(needs_review[:20]),
    ]
    return "\n".join(md)
