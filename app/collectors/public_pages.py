from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.collectors.common import normalize_lead
from app.config import Settings

PUBLIC_SOURCES = {
    "ProductionBase": "https://www.productionbase.co.uk/jobs",
    "Mandy": "https://www.mandy.com/uk/jobs",
    "TheDots": "https://the-dots.com/jobs/search/photographer",
    "Creativepool": "https://creativepool.com/jobs",
    "Twine": "https://www.twine.net/jobs",
    "PeoplePerHour": "https://www.peopleperhour.com/freelance-photographer-jobs",
    "ArtsJobs": "https://www.artsjobs.org.uk/jobs",
    "CreativeAccess": "https://creativeaccess.org.uk/opportunities",
    "ScreenSkills": "https://www.screenskills.com/jobs",
    "BFI": "https://www.bfi.org.uk/get-involved/jobs",
}


def _allowed_by_robots(user_agent: str, url: str, client: httpx.Client) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        resp = client.get(robots_url)
        if resp.status_code >= 400:
            return False
        rp.parse(resp.text.splitlines())
        return rp.can_fetch(user_agent, url)
    except Exception:
        return False


def _cache_path(cache_dir: str, url: str) -> Path:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return Path(cache_dir) / f"{key}.json"


def _fetch_cached_html(client: httpx.Client, settings: Settings, url: str) -> str | None:
    path = _cache_path(settings.public_page_cache_dir, url)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")).get("html")
    try:
        response = client.get(url)
        response.raise_for_status()
        path.write_text(json.dumps({"html": response.text}), encoding="utf-8")
        time.sleep(settings.request_delay_seconds)
        return response.text
    except Exception:
        return None


def _extract_cards(base_url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards: list[dict] = []
    for node in soup.select("article, .job, .job-card, li, .listing")[:50]:
        title_node = node.select_one("h1, h2, h3, a")
        if not title_node:
            continue
        title = title_node.get_text(" ", strip=True)
        if len(title) < 6:
            continue
        link = title_node.get("href")
        cards.append(
            {
                "title": title,
                "description": node.get_text(" ", strip=True)[:1000],
                "source_url": urljoin(base_url, link) if link else base_url,
                "apply_url": urljoin(base_url, link) if link else base_url,
                "location": "United Kingdom",
            }
        )
    return cards


def run(settings: Settings) -> dict[str, Any]:
    leads: list[dict] = []
    errors: list[str] = []
    with httpx.Client(timeout=settings.request_timeout, headers={"User-Agent": settings.user_agent}) as client:
        for source, url in PUBLIC_SOURCES.items():
            if not _allowed_by_robots(settings.user_agent, url, client):
                errors.append(f"{source}: blocked by robots.txt")
                continue
            html = _fetch_cached_html(client, settings, url)
            if not html:
                errors.append(f"{source}: failed to fetch")
                continue
            cards = _extract_cards(url, html)
            if not cards:
                errors.append(f"{source}: no cards extracted")
            for card in cards:
                leads.append(normalize_lead(source, "public_page", card))
    return {"source": "public_pages", "leads": leads, "errors": errors}
