from app.classify import classify_lead


def test_classifies_wedding_second_shooter():
    result = classify_lead("Wedding second shooter needed", "Paid role")
    assert result.category == "wedding"
    assert result.role_type == "second_shooter"


def test_classifies_irrelevant_role():
    result = classify_lead("Radiographer role", "Hospital post")
    assert result.category == "irrelevant"
