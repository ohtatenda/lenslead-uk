from __future__ import annotations

HIRING_INTENT_TERMS = {
    "hiring",
    "wanted",
    "looking for",
    "need",
    "needed",
    "vacancy",
    "vacancies",
    "job",
    "jobs",
    "role",
    "position",
    "opportunity",
    "apply",
    "recruiting",
    "freelance project",
    "contract role",
    "immediate start",
}

NON_HIRING_TERMS = {
    "tips",
    "guide",
    "ideas",
    "inspiration",
    "portfolio",
    "course",
    "training",
    "tutorial",
    "services",
    "agency",
    "blog",
    "best photographers",
}


def has_hiring_intent(title: str = "", description: str = "") -> bool:
    text = f"{title} {description}".lower()
    has_positive = any(term in text for term in HIRING_INTENT_TERMS)
    has_negative = any(term in text for term in NON_HIRING_TERMS)
    return has_positive and not has_negative
