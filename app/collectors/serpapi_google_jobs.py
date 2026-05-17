from __future__ import annotations

from typing import Any

import httpx

from app.collectors.common import normalize_lead
from app.config import Settings

DISCOVERY_SITES = [
    "indeed.com",
    "linkedin.com",
    "totaljobs.com",
    "jobsite.co.uk",
    "glassdoor.co.uk",
    "jooble.org",
    "talent.com",
    "simplyhired.co.uk",
    "productionbase.co.uk",
    "mandy.com",
    "the-dots.com",
    "creativepool.com",
    "twine.net",
    "peopleperhour.com",
    "artsjobs.org.uk",
    "creativeaccess.org.uk",
    "screenskills.com",
    "bfi.org.uk",
]


def run(settings: Settings) -> dict[str, Any]:
    if not settings.serpapi_api_key:
        return {"source": "serpapi_google_jobs", "leads": [], "errors": ["SERPAPI_API_KEY not set"]}
    leads: list[dict] = []
    errors: list[str] = []
    with httpx.Client(timeout=settings.request_timeout, headers={"User-Agent": settings.user_agent}) as client:
        for category, queries in settings.all_queries.items():
            for query in queries[:4]:
                try:
                    response = client.get(
                        "https://serpapi.com/search.json",
                        params={
                            "engine": "google_jobs",
                            "q": f"{query} UK",
                            "hl": "en",
                            "api_key": settings.serpapi_api_key,
                        },
                    )
                    response.raise_for_status()
                    jobs = response.json().get("jobs_results", [])
                    for job in jobs:
                        leads.append(
                            normalize_lead(
                                "SerpAPI Google Jobs",
                                "search_api",
                                {
                                    "title": job.get("title"),
                                    "company": job.get("company_name"),
                                    "location": job.get("location"),
                                    "description": job.get("description"),
                                    "source_url": (job.get("related_links") or [{}])[0].get("link"),
                                    "apply_url": (job.get("apply_options") or [{}])[0].get("link"),
                                    "posted_date": job.get("detected_extensions", {}).get("posted_at"),
                                    "category": category,
                                    "pay_text": job.get("detected_extensions", {}).get("salary"),
                                },
                            )
                        )
                except Exception as exc:
                    errors.append(f"{query}: {exc}")

        for site in DISCOVERY_SITES:
            try:
                response = client.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google",
                        "q": f"site:{site} photographer videographer jobs UK",
                        "hl": "en",
                        "api_key": settings.serpapi_api_key,
                    },
                )
                response.raise_for_status()
                for result in response.json().get("organic_results", [])[:5]:
                    leads.append(
                        normalize_lead(
                            "SerpAPI Discovery",
                            "search_api",
                            {
                                "title": result.get("title"),
                                "company": site,
                                "location": "United Kingdom",
                                "description": result.get("snippet"),
                                "source_url": result.get("link"),
                                "apply_url": result.get("link"),
                                "category": "general",
                            },
                        )
                    )
            except Exception as exc:
                errors.append(f"{site}: {exc}")
    return {"source": "serpapi_google_jobs", "leads": leads, "errors": errors}
