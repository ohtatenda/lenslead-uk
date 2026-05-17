from app.manual_intake import parse_manual_text, save_manual_input


def test_manual_parse_extracts_fields():
    raw = "Wedding photographer needed in London. £350 per day. Contact test@example.com on 20/06/2026."
    parsed = parse_manual_text(raw)
    assert "Wedding photographer needed" in parsed["title"]
    assert parsed["location"].lower() == "london"
    assert "£350" in parsed["pay_text"]
    assert parsed["contact_email"] == "test@example.com"


def test_manual_save(session):
    raw = "Event videographer needed in Manchester. Paid £500 day rate. contact@demo.com"
    lead = save_manual_input(session, raw)
    assert lead is not None
    assert lead.source == "manual"
