"""Fixed texts. Alert templates are filled only from the event payload (PRD v2 F9.6)."""

from __future__ import annotations

CONSENT_VERSION = "c1"
APP_URL = "https://recall-radar.us"
VIN_HANDOFF = ("I can't check a specific VIN. NHTSA's lookup shows unrepaired recalls for a VIN: "
               "https://www.nhtsa.gov/recalls — Recall Radar does not check it.")
REPORT_HOWTO = ("To report a safety problem to NHTSA, use https://www.nhtsa.gov/report-a-safety-problem — "
                "your complaint is submitted only after you complete NHTSA's form.")
NO_DIAGNOSIS = ("I can't diagnose a vehicle or say whether it is safe to drive. I can show what other people "
                "reported to NHTSA and the official recalls. " + REPORT_HOWTO)
HELP = ("Recall Radar commands: WATCH <year make model>, STATUS, DETAILS, PAUSE, RESUME, STOP, DELETE, HELP. "
        "You can also ask about reported problems, recalls or remedies for your vehicle.")
SCOPE = ("I answer questions about public NHTSA data for a car model: reported problems, complaint counts, "
         "recalls and their official remedy text, and how to report a problem to NHTSA. "
         "Try: what problems do 2019 Jeep Cherokee owners report?")
CLAIM_HELP = ("I can't give insurance or legal advice, but I can point you to public records people often gather: "
              "the NHTSA complaints and recall campaigns for your model (ask me, or see the one-page summary on "
              "https://recall-radar.us), your car's own recall status by VIN at https://www.nhtsa.gov/recalls, and "
              "your repair and dealer receipts. You can also file your own complaint at "
              "https://www.nhtsa.gov/report-a-safety-problem")
GROUP_REFUSAL = "Recall Radar only works in one-to-one chats."
PHONE_REFUSAL = "Please don't send phone numbers. To watch a vehicle, reply WATCH <year make model>."


def consent(year: int, make: str, model: str, tz: str) -> str:
    return (f"Recall Radar can send you at most one update a day about the {year} {make} {model} when NHTSA "
            f"publishes new complaints or recalls for it, never between 21:00 and 08:00 ({tz}). "
            f"Reply YES to start. Reply STOP at any time to stop.")


def link(year: int, make: str, model: str) -> str:
    from urllib.parse import urlencode
    return f"{APP_URL}/vehicle?{urlencode({'make': make, 'model': model, 'year': year})}"


def alert(p: dict) -> str:
    """new_complaints payload → the PRD template; every value comes from the payload."""
    return (f"Recall Radar found {p['n']} newly published distinct complaints mentioning {p['issue']} for "
            f"{p['year']} {p['make']} {p['model']} between {p['start']} and {p['end']}. View: {p['link']}. "
            f"Reply DETAILS or STOP.")


def campaign_alert(p: dict) -> str:
    return (f"NHTSA published recall campaign {p['campno']} for the {p['year']} {p['make']} {p['model']} "
            f"(model-level, not a specific car). View: {p['link']}. Reply DETAILS or STOP.")
