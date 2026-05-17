from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScoreResult:
    score: int
    reasons: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


def score_lead(title: str, description: str, category: str, location: str = "", pay_text: str = "") -> ScoreResult:
    text = f"{title} {description}".lower()
    score = 40
    reasons: list[str] = []
    red_flags: list[str] = []

    positive_terms = [
        ("wedding photographer", 18, "Wedding role keyword"),
        ("wedding videographer", 18, "Wedding video role keyword"),
        ("second shooter", 15, "Second shooter opportunity"),
        ("associate", 10, "Associate role"),
        ("event photographer", 14, "Event role keyword"),
        ("event videographer", 14, "Event video role keyword"),
        ("corporate", 8, "Corporate event/commercial relevance"),
        ("fashion", 7, "Fashion/editorial relevance"),
        ("brand", 7, "Brand content relevance"),
    ]
    for term, points, reason in positive_terms:
        if term in text:
            score += points
            reasons.append(reason)

    if category in {"wedding", "event", "general"}:
        score += 8
        reasons.append("Target category match")

    if any(k in (pay_text or "").lower() for k in ["£", "day rate", "per hour", "salary"]):
        score += 10
        reasons.append("Clear pay signal")
    else:
        score -= 8
        red_flags.append("No clear pay")

    if location and "uk" in location.lower() or any(
        city in location.lower() for city in ["london", "manchester", "birmingham", "leeds", "bristol"]
    ):
        score += 8
        reasons.append("Clear UK location")
    else:
        score -= 8
        red_flags.append("No clear location")

    if any(w in text for w in ["apply", "email", "contact", "portfolio"]):
        score += 6
        reasons.append("Has contact/apply signal")

    negative_terms = [
        ("unpaid", 22, "Unpaid or collab-only"),
        ("volunteer", 20, "Volunteer-only"),
        ("expired", 20, "Expired listing"),
        ("radiographer", 30, "Irrelevant role"),
        ("retail assistant", 25, "Irrelevant role"),
        ("school teacher", 25, "Irrelevant role"),
        ("wire transfer", 30, "Suspicious listing pattern"),
    ]
    for term, penalty, flag in negative_terms:
        if term in text:
            score -= penalty
            red_flags.append(flag)

    if category == "irrelevant":
        score = min(score, 10)
        red_flags.append("Classified as irrelevant")
    if category == "needs_review":
        score -= 10
        red_flags.append("Needs manual review")

    score = max(0, min(100, score))
    return ScoreResult(score=score, reasons=reasons[:8], red_flags=red_flags[:8])
