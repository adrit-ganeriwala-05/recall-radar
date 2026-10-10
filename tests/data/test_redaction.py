"""A2: complaint text redaction before storage (PROJECT_SPEC §10, CONTRACTS §8)."""

import os
import string
from pathlib import Path

import pytest

from recall_radar.data.redact import has_pii, redact

_SEP = "()-.+"
_EDGE = ",;:!?\"'"


def independent_leaks(text: str) -> list[str]:
    """Leak finder that shares no code or patterns with redact.py (tokens, not regexes)."""
    tokens = [t.strip(_EDGE) for t in text.split()]
    leaks = [t for t in tokens if "@" in t and "." in t.split("@")[-1]
             and t.split("@")[-1].split(".")[0] != ""
             and all(c.isalnum() or c == "-" for c in t.split("@")[-1].rstrip(".").replace(".", ""))
             and t.rstrip(".").rsplit(".", 1)[-1].isalpha() and len(t.rstrip(".").rsplit(".", 1)[-1]) >= 2]
    vin_chars = set(string.ascii_uppercase + string.digits) - set("IOQ")
    leaks += [t for t in tokens if len(t.rstrip(".")) == 17 and set(t.rstrip(".").upper()) <= vin_chars
              and any(c.isdigit() for c in t)]
    raw = text.split()
    for width in (1, 2, 3, 4):  # phone numbers split over up to 4 tokens: +1 (404) 555 0134
        for i in range(len(tokens) - width + 1):
            window = tokens[i:i + width]
            if not all(w and all(c.isdigit() or c in _SEP for c in w) for w in window):
                continue
            if any(r.endswith((",", ";")) for r in raw[i:i + width - 1]):
                continue  # "12345, 67890" is a list (mileages, dates), not one number
            digits = "".join(c for w in window for c in w if c.isdigit())
            if len(digits) == 10 or (len(digits) == 11 and digits[0] == "1"):
                leaks.append(" ".join(window))
            elif len(digits) == 7 and [sum(c.isdigit() for c in g) for g in
                                       "".join(c if c.isdigit() else " " for c in " ".join(window)).split()] == [3, 4]:
                leaks.append(" ".join(window))  # local number: 555-0134, 555 0134
    return leaks


@pytest.mark.parametrize(
    ("text", "gone", "token"),
    [
        ("EMAIL ME AT JANE_DOE+cars@mail.example.org TODAY", "JANE_DOE", "[EMAIL]"),
        ("CALL (404) 555-0134 ANYTIME", "555-0134", "[PHONE]"),
        ("CALL 404.555.0134", "555.0134", "[PHONE]"),
        ("CALL +1 404-555-0134", "555-0134", "[PHONE]"),
        ("CALL 4045550134 OR 14045550134", "4045550134", "[PHONE]"),
        ("CALL 404 555 0134.", "555 0134", "[PHONE]"),
        ("CALL (404- 555-0134) TODAY", "555-0134", "[PHONE]"),
        ("PH:1-404-555-0134.", "555-0134", "[PHONE]"),
        ("REACH ME AT [XXX]@MAIL.COM", "MAIL.COM", "[EMAIL]"),
        ("CALL 404 555 - 0134.", "0134", "[PHONE]"),
        ("CALL (404), 555-0134 NOW", "555-0134", "[PHONE]"),
        ("ID: 40455    50134 - END", "50134", "[PHONE]"),
        ("CALL 555-0134 AFTER 5", "555-0134", "[PHONE]"),
        ("CALL 555 0134.", "555 0134", "[PHONE]"),
        ("CALL 555 - 0134 OR 555 (0134 OR 555    0134", "0134", "[PHONE]"),
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
    assert independent_leaks(out) == []


@pytest.mark.parametrize(
    "text",
    [
        "THE CAR STALLED AT 65 MPH ON THE ROAD",
        "AT 30 MILES DOWN THE ROAD THE ENGINE QUIT",
        "THE 2017 MODEL HAS 4 DOORS",
        "RECALL 17V123000 WAS PERFORMED",
        "TRANSMISSIONSLIPPING IS A LONG WORD",
        "MODEL YEARS 2017 2018 2019 AT 65000 MILES",
        "IT FAILED @9:30PM AND COST @$100.00",
        "ODINO 11234567 AND RECALL 19V-123",
        "BETWEEN 2017-2018 AT 100 MPH",
        "ON 10/12/2017 AND 1.5 2017",
    ],
)
def test_keeps_vehicle_facts(text):
    assert redact(text) == text


def test_independent_checker_catches_raw_details():
    raw = "CALL 4045550134 OR (404) 555-0134 OR JANE@MAIL.COM VIN 1FTFW1ET5DFC10312"
    assert len(independent_leaks(raw)) >= 4
    assert independent_leaks("MODEL YEARS 2017 2018 2019 AT 65000 MILES") == []
    assert independent_leaks("IT FAILED @9:30PM AND COST @$100.00") == []
    assert independent_leaks("THE (@#$%).AA CAR") == []
    assert independent_leaks("AT 2017 @9:30.AM TODAY") == []


def test_none_passes_through():
    assert redact(None) is None


def test_stored_text_is_redacted(con):
    (text,) = con.execute("SELECT descr_redacted FROM complaint_doc WHERE odino='10000027'").fetchone()
    for leaked in ("JOHN", "SMITH", "555-0134", "@", "1FTFW1ET5DFC10312", "123 MAIN"):
        assert leaked not in text
    assert "65 MPH ON THE ROAD" in text
    assert not has_pii(text)


@pytest.mark.real_data
def test_real_stored_texts_have_no_leaks():
    import duckdb

    db = Path(os.environ.get("RR_DATA_DIR", "data")) / "recall_radar.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    texts = [t for (t,) in con.execute("SELECT descr_redacted FROM complaint_doc WHERE descr_redacted <> ''").fetchall()]
    con.close()
    leaking = sum(1 for t in texts if independent_leaks(t) or has_pii(t))
    assert leaking == 0, f"{leaking} of {len(texts)} stored texts still contain an email, phone or VIN"
