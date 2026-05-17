from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    database_url: str = Field(default="sqlite:///data/lenslead.db")
    reed_api_key: str | None = Field(default=None)
    adzuna_app_id: str | None = Field(default=None)
    adzuna_app_key: str | None = Field(default=None)
    serpapi_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    user_agent: str = Field(default="LensLeadUK/1.0 (+local-dev)")
    request_timeout: int = Field(default=20)
    request_delay_seconds: float = Field(default=1.0)
    max_pages_per_source: int = Field(default=3)
    public_page_cache_dir: str = Field(default="data/http_cache")
    source_toggles: Dict[str, bool] = Field(
        default_factory=lambda: {
            "reed": True,
            "adzuna": True,
            "serpapi_google_jobs": True,
            "public_pages": True,
            "manual": True,
        }
    )
    locations: List[str] = Field(
        default_factory=lambda: [
            "United Kingdom",
            "London",
            "Ilford",
            "East London",
            "Essex",
            "Kent",
            "Surrey",
            "Hertfordshire",
            "Birmingham",
            "Manchester",
            "Bristol",
            "Leeds",
            "Brighton",
            "Cambridge",
            "Oxford",
            "Remote",
            "Hybrid",
        ]
    )
    wedding_queries: List[str] = Field(
        default_factory=lambda: [
            "wedding photographer",
            "wedding videographer",
            "second shooter wedding",
            "associate wedding photographer",
            "lead wedding photographer",
            "freelance wedding photographer",
            "freelance wedding videographer",
            "wedding content creator",
            "wedding film editor",
            "wedding photography assistant",
            "wedding videography assistant",
            "wedding photographer wanted",
            "wedding videographer wanted",
        ]
    )
    event_queries: List[str] = Field(
        default_factory=lambda: [
            "event photographer",
            "event videographer",
            "corporate event photographer",
            "conference photographer",
            "festival videographer",
            "PR event photographer",
            "sports event photographer",
            "nightlife photographer",
            "event content creator",
            "camera operator event",
        ]
    )
    general_queries: List[str] = Field(
        default_factory=lambda: [
            "photographer",
            "videographer",
            "photographer videographer",
            "content creator",
            "video editor",
            "photo editor",
            "retoucher",
            "camera operator",
            "director of photography",
            "filmmaker",
            "brand photographer",
            "product photographer",
            "property photographer",
            "marketing videographer",
        ]
    )

    @property
    def all_queries(self) -> Dict[str, List[str]]:
        return {
            "wedding": self.wedding_queries,
            "event": self.event_queries,
            "general": self.general_queries,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///data/lenslead.db"),
        reed_api_key=os.getenv("REED_API_KEY"),
        adzuna_app_id=os.getenv("ADZUNA_APP_ID"),
        adzuna_app_key=os.getenv("ADZUNA_APP_KEY"),
        serpapi_api_key=os.getenv("SERPAPI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_agent=os.getenv("LENSLEAD_USER_AGENT", "LensLeadUK/1.0 (+local-dev)"),
    )
    Path("data").mkdir(exist_ok=True)
    Path(settings.public_page_cache_dir).mkdir(parents=True, exist_ok=True)
    return settings
