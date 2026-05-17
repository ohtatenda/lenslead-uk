from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.collectors import adzuna, public_pages, reed, serpapi_google_jobs
from app.config import get_settings
from app.db import get_session, init_db
from app.dedupe import is_duplicate
from app.models import Lead, Run
from app.relevance import has_hiring_intent


def _save_leads(session: Session, leads: list[dict]) -> int:
    saved = 0
    for payload in leads:
        if not has_hiring_intent(payload.get("title", ""), payload.get("description", "")):
            continue
        if is_duplicate(session, payload):
            continue
        session.add(Lead(**payload))
        saved += 1
    session.flush()
    return saved


def run_all_collectors() -> dict:
    settings = get_settings()
    init_db()
    collectors = [
        ("reed", reed.run),
        ("adzuna", adzuna.run),
        ("serpapi_google_jobs", serpapi_google_jobs.run),
        ("public_pages", public_pages.run),
    ]
    summary: dict[str, dict] = {}
    with get_session() as session:
        for source_name, func in collectors:
            if not settings.source_toggles.get(source_name, True):
                continue
            run_row = Run(source_name=source_name, started_at=datetime.utcnow())
            session.add(run_row)
            try:
                result = func(settings)
                leads = result.get("leads", [])
                errors = result.get("errors", [])
                saved = _save_leads(session, leads)
                run_row.finished_at = datetime.utcnow()
                run_row.success = "false" if errors else "true"
                run_row.leads_found = len(leads)
                run_row.leads_saved = saved
                run_row.error_message = "\n".join(errors) if errors else None
                summary[source_name] = {"found": len(leads), "saved": saved, "errors": errors}
            except Exception as exc:
                run_row.finished_at = datetime.utcnow()
                run_row.success = "false"
                run_row.error_message = str(exc)
                summary[source_name] = {"found": 0, "saved": 0, "errors": [str(exc)]}
    return summary


if __name__ == "__main__":
    output = run_all_collectors()
    print("LensLead UK collector run complete.")
    for source, stats in output.items():
        print(f"{source}: found={stats['found']} saved={stats['saved']} errors={len(stats['errors'])}")
