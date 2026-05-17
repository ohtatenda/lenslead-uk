from app.relevance import has_hiring_intent


def test_hiring_intent_true_for_real_job_post():
    assert has_hiring_intent(
        "Wedding videographer wanted - paid role",
        "We are hiring for a freelance position in London. Apply by email.",
    )


def test_hiring_intent_false_for_informational_post():
    assert not has_hiring_intent(
        "Best wedding photography tips",
        "A guide with ideas and inspiration for your portfolio.",
    )
