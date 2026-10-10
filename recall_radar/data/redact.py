"""Complaint text redaction (owner: A). Applied to CDESCR before anything is stored.

Removes emails, phone numbers, 17-character VIN patterns, street addresses and "my name is …"
(PROJECT_SPEC §10). Over-redaction is acceptable; leaking a person's details is not.
"""

from __future__ import annotations

import re

# Any non-space local part: NHTSA sometimes masks it already ("[XXX]@MAIL.COM").
_EMAIL = re.compile(r"[^\s@]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
# VIN alphabet excludes I, O, Q; must contain a digit so long plain words are left alone.
_VIN = re.compile(r"\b(?=[A-HJ-NPR-Z0-9]*\d)[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE)
# Phone: 10 digits (or 11 starting with 1) in any grouping, at most three separator characters
# between digits, not touching other digits. Catches "4045550134", "404- 555-0134",
# "(404) 555- 0134" and "40455 50134"; 10-digit part numbers in 5-5 form are redacted too.
_SEPS = r"(?:\s+|[().+-]){0,3}"  # a whitespace run counts as one separator
_PHONE = re.compile(
    rf"(?<!\d)(?:\+?1{_SEPS})?\(?(?:\d{_SEPS}){{9}}\d(?!\d)"
    r"|\(\d{3}\),\s*\d{3}[\s.-]{0,3}\d{4}(?!\d)"  # "(404), 555-0134"
)
_SUFFIX = (
    r"STREET|ST|AVENUE|AVE|ROAD|RD|BOULEVARD|BLVD|DRIVE|DR|LANE|LN|COURT|CT|PLACE|PL|"
    r"PARKWAY|PKWY|CIRCLE|CIR|TERRACE|TER|TRAIL|TRL|HIGHWAY|HWY"
)
# A house number, 1-4 words, then a street suffix. Speeds and distances ("65 MPH ON THE ROAD")
# are not addresses.
_ADDRESS = re.compile(
    rf"\b\d{{1,6}}(?!\s*(?:MPH|MILES?|MI|KM|KPH|KMH|FEET|FT|YARDS?|MINUTES?|HOURS?|DAYS?)\b)"
    rf"(?:\s+[A-Za-z0-9.'-]+){{1,4}}?\s+(?:{_SUFFIX})\b\.?",
    re.IGNORECASE,
)
_NAME = re.compile(r"\b(my\s+name\s+is)\s+[A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]*)?", re.IGNORECASE)


def redact(text: str | None) -> str | None:
    if text is None:
        return None
    text = _EMAIL.sub("[EMAIL]", text)
    text = _VIN.sub("[VIN]", text)
    text = _PHONE.sub("[PHONE]", text)
    text = _ADDRESS.sub("[ADDRESS]", text)
    text = _NAME.sub(r"\1 [NAME]", text)
    return text


def has_pii(text: str) -> bool:
    """True if an email, phone number or VIN pattern survives (CONTRACTS §8 check)."""
    return bool(_EMAIL.search(text) or _VIN.search(text) or _PHONE.search(text))
