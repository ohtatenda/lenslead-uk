from __future__ import annotations

from typing import Any

import httpx

from app.collectors.common import normalize_lead
from app.config import Settings


def run(settings: Settings) -> dict[str, Any]:
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        return {"source": "adzuna", "leads": [], "errors": ["Adzuna credentials missing"]}
    leads: list[dict] = []
    errors: list[str] = []
    with httpx.Client(timeout=settings.request_timeout, headers={"User-Agent": settings.user_agent}) as client:
        for category, queries in settings.all_queries.items():
            for query in queries[:4]:
                try:
                    url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
                    response = client.get(
                        url,
                        params={
                            "app_id": settings.adzuna_app_id,
                            "app_key": settings.adzuna_app_key,
                            "results_per_page": 20,
                            "what": query,
                            "where": "United Kingdom",
                            "content-type": "application/json",
                        },
                    )
                    response.raise_for_status()
                    for job in response.json().get("results", []):
                        leads.append(
                            normalize_lead(
                                "Adzuna",
                                "api",
                                {
                                    "title": job.get("title"),
                                    "company": (job.get("company") or {}).get("display_name"),
                                    "location": (job.get("location") or {}).get("display_name"),
                                    "description": job.get("description"),
                                    "source_url": job.get("redirect_url"),
                                    "apply_url": job.get("redirect_url"),
                                    "pay_min": job.get("salary_min"),
                                    "pay_max": job.get("salary_max"),
                                    "pay_text": f"£{job.get('salary_min') or ''}-£{job.get('salary_max') or ''}",
                                    "posted_date": job.get("created"),
                                    "category": category,
                                    "job_type": job.get("contract_type"),
                                },
                            )
                        )
                except Exception as exc:
                    errors.append(f"{query}: {exc}")
    return {"source": "adzuna", "leads": leads, "errors": errors}
