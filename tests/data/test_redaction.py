"""A2: complaint text redaction before storage (PROJECT_SPEC §10, CONTRACTS §8)."""

import pytest

from recall_radar.data.redact import has_pii, redact


@pytest.mark.parametrize(
    ("text", "gone", "token"),
    [
        ("EMAIL ME AT JANE_DOE+cars@mail.example.org TODAY", "JANE_DOE", "[EMAIL]"),
        ("CALL (404) 555-0134 ANYTIME", "555-0134", "[PHONE]"),
        ("CALL 404.555.0134", "555.0134", "[PHONE]"),
        ("CALL +1 404-555-0134", "555-0134", "[PHONE]"),
        ("MY VIN IS 1FTFW1ET5DFC10312 PLEASE CHECK", "1FTFW1ET5DFC10312", "[VIN]"),
        ("vin 1ftfw1et5dfc10312.", "1ftfw1et5dfc10312", "[VIN]"),
        ("I LIVE AT 4521 NORTH OAK AVE IN TOWN", "4521 NORTH OAK", "[ADDRESS]"),
        ("SEND TO 12 ELM ST.", "12 ELM", "[ADDRESS]"),
        ("my name is Maria Garcia and the car stalled", "Maria Garcia", "[NAME]"),
        ("MY NAME IS JOHN.", "JOHN", "[NAME]"),
    ],
)
def test_redacts_personal_details(text, gone, token):
    out = redact(text)
    assert gone not in out and token in out
    assert not has_pii(out)


@pytest.mark.parametrize(
    "text",
    [
        "THE CAR STALLED AT 65 MPH ON THE ROAD",
        "AT 30 MILES DOWN THE ROAD THE ENGINE QUIT",
        "THE 2017 MODEL HAS 4 DOORS",
        "RECALL 17V123000 WAS PERFORMED",
        "TRANSMISSIONSLIPPING IS A LONG WORD",
    ],
)
def test_keeps_vehicle_facts(text):
    assert redact(text) == text


def test_none_passes_through():
    assert redact(None) is None


def test_stored_text_is_redacted(con):
    (text,) = con.execute("SELECT descr_redacted FROM complaint_doc WHERE odino='10000027'").fetchone()
    for leaked in ("JOHN", "SMITH", "555-0134", "@", "1FTFW1ET5DFC10312", "123 MAIN"):
        assert leaked not in text
    assert "65 MPH ON THE ROAD" in text
    assert not has_pii(text)
