from app.scoring import score_lead


def test_scoring_high_quality_wedding_lead():
    result = score_lead(
        title="Wedding Photographer Needed",
        description="Paid role, London, apply by email, second shooter wanted",
        category="wedding",
        location="London, UK",
        pay_text="£400 per day",
    )
    assert 70 <= result.score <= 100
    assert result.reasons


def test_scoring_penalizes_unpaid_irrelevant():
    result = score_lead(
        title="Volunteer retail assistant",
        description="unpaid volunteer role",
        category="irrelevant",
        location="",
        pay_text="",
    )
    assert 0 <= result.score <= 20
    assert result.red_flags
