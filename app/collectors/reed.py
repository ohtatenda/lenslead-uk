from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.collectors.common import normalize_lead


def run(settings: Settings) -> dict[str, Any]:
    if not settings.reed_api_key:
        return {"source": "reed", "leads": [], "errors": ["REED_API_KEY not set"]}
    auth = ("", settings.reed_api_key)
    leads: list[dict] = []
    errors: list[str] = []
    with httpx.Client(timeout=settings.request_timeout, headers={"User-Agent": settings.user_agent}, auth=auth) as client:
        for category, queries in settings.all_queries.items():
            for query in queries[:4]:
                try:
                    response = client.get(
                        "https://www.reed.co.uk/api/1.0/search",
                        params={"keywords": query, "locationName": "United Kingdom", "resultsToTake": 20},
                    )
                    response.raise_for_status()
                    for job in response.json().get("results", []):
                        leads.append(
                            normalize_lead(
                                "Reed",
                                "api",
                                {
                                    "title": job.get("jobTitle"),
                                    "company": (job.get("employerName") or ""),
                                    "location": job.get("locationName"),
                                    "description": job.get("jobDescription"),
                                    "source_url": job.get("jobUrl"),
                                    "apply_url": job.get("jobUrl"),
                                    "pay_text": f"{job.get('minimumSalary') or ''}-{job.get('maximumSalary') or ''}",
                                    "pay_min": job.get("minimumSalary"),
                                    "pay_max": job.get("maximumSalary"),
                                    "posted_date": job.get("date"),
                                    "category": category,
                                    "job_type": job.get("jobType"),
                                },
                            )
                        )
                except Exception as exc:
                    errors.append(f"{query}: {exc}")
    return {"source": "reed", "leads": leads, "errors": errors}
