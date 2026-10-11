"""Questions in chat (PRD v2 F9.7). Deterministic keyword routing (no GEMINI_API_KEY / google-genai here),
only allowlisted tools, ≤ 3 tool calls, and every number in a reply must appear in tool output (validated).
Retrieved complaint text is data: replies cite complaint ids and links, never quote text as instructions."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from typing import Any

from . import templates as T
from .analysis import Analysis, find_vehicle

CONTEXT_S = 30 * 60
MAX_TOOL_CALLS = 3

INTENTS: list[tuple[str, re.Pattern]] = [
    ("vin", re.compile(r"\bvin\b|\b[A-HJ-NPR-Z0-9]{17}\b", re.I)),
    ("diagnosis", re.compile(r"\b(safe to drive|is it safe|diagnos|what('?s| is) wrong|how (do|can) i fix|repair it)\b", re.I)),
    ("how_to_report", re.compile(r"\b(how (do|can) i|where (do|can) i) (report|file|submit)\b|\breport (a|this) (problem|complaint)\b", re.I)),
    ("send_document", re.compile(r"\b(send|email|pdf|document|report)\b.*\b(me|report|summary|pdf)\b", re.I)),
    ("remedy", re.compile(r"\b(remedy|fix for the recall|what will (they|the dealer) do)\b", re.I)),
    ("explain_recall", re.compile(r"\b(explain|what (does|is)) .*\b(recall|campaign)\b|\b\d{2}V\d{3}\d{0,3}\b", re.I)),
    ("recall_count", re.compile(r"\bhow many recalls?\b|\brecalls?\b", re.I)),
    ("trend", re.compile(r"\b(trend|over time|per month|by month|increas|decreas)\w*", re.I)),
    ("count", re.compile(r"\bhow many\b|\bcount\b|\bnumber of\b", re.I)),
    ("similar", re.compile(r"\b(similar|same problem|anyone else|others report)\b", re.I)),
    ("problems", re.compile(r"\b(problems?|issues?|complaints?|reported)\b", re.I)),
]


def route_intent(text: str) -> str | None:
    for name, rx in INTENTS:
        if rx.search(text):
            return name
    return None


def numbers_grounded(reply: str, tool_text: str) -> bool:
    """Every number in the reply (thousands separators removed) occurs in the tool output."""
    have = set(re.findall(r"\d+", tool_text.replace(",", "")))
    return all(n in have for n in re.findall(r"\d+", reply.replace(",", "")))


class Tools:
    """Allowlist. Each call returns data + scope + snapshot date + source; at most MAX_TOOL_CALLS per question."""

    ALLOWED = ("vehicle_lookup", "complaint_search", "complaint_count", "recall_lookup", "investigation_lookup",
               "source_detail", "report_get")

    def __init__(self, a: Analysis):
        self.a, self.calls, self.outputs = a, 0, []

    def call(self, name: str, **kw: Any) -> dict | None:
        if name not in self.ALLOWED:
            raise PermissionError(f"tool {name} is not allowlisted")
        if self.calls >= MAX_TOOL_CALLS:
            return None
        self.calls += 1
        mk, md, yr = kw["vehicle"]
        if name in ("vehicle_lookup", "complaint_count", "recall_lookup"):
            out = self.a.get("/api/vehicle", make=mk, model=md, year=yr)
        elif name in ("investigation_lookup", "report_get"):
            out = self.a.get("/api/report", make=mk, model=md, year=yr)
        else:
            out = self.a.get("/api/symptom-index", make=mk, model=md, year=yr)
        if out is not None:
            self.outputs.append(json.dumps(out))
        return out

    def derived(self, value: int) -> int:
        """A count computed from tool output (e.g. len of a list it returned) is grounded too."""
        self.outputs.append(str(value))
        return value


def answer(text: str, ctx: dict | None, a: Analysis, router: Callable[[str], str | None] = route_intent,
           timeout_s: float = 15) -> tuple[str, dict | None]:
    """→ (reply, new context). Context = vehicle + last campno, expires after 30 minutes."""
    now = time.time()
    if ctx and ctx.get("expires_at", 0) < now:
        ctx = None
    started = time.time()
    try:
        intent = router(text)
    except Exception:  # noqa: BLE001 — a model/router failure falls back to keywords
        intent = None
    if intent is None or time.time() - started > timeout_s:
        intent = route_intent(text)
    if intent == "vin":
        return T.VIN_HANDOFF, ctx
    if intent == "diagnosis":
        return T.NO_DIAGNOSIS, ctx
    if intent == "how_to_report":
        return T.REPORT_HOWTO, ctx
    found = find_vehicle(text, a)
    vehicle = found or ((ctx["make"], ctx["model"], ctx["model_year"]) if ctx else None)
    if vehicle is None:
        return "Which vehicle? Reply with the model year, make and model, for example: 2019 Jeep Cherokee.", ctx
    mk, md, yr = vehicle
    new_ctx = {"make": mk, "model": md, "model_year": yr, "campno": (ctx or {}).get("campno"), "expires_at": now + CONTEXT_S}
    tools = Tools(a)
    reply = _reply(intent or "problems", text, vehicle, tools, new_ctx)
    if not numbers_grounded(reply, " ".join(tools.outputs) + f" {yr}"):
        reply = f"I couldn't check those numbers, so here is the source instead: {T.link(yr, mk, md)}"
    return reply, new_ctx


def _reply(intent: str, text: str, v: tuple[str, str, int], tools: Tools, ctx: dict) -> str:
    mk, md, yr = v
    name, url = f"{yr} {mk} {md}", T.link(yr, mk, md)
    if intent == "send_document":
        return f"Here is the one-page summary as a link (not a file): {url.replace('/vehicle?', '/vehicle/report?')}"
    if intent in ("count", "problems", "trend", "similar"):
        veh = tools.call("vehicle_lookup", vehicle=v)
        if not veh:
            return f"The data service isn't answering right now. Source: {url}"
        asof = veh["provenance"].get("data_as_of") or "the current snapshot"
        groups = veh["components"]
        if intent == "count":
            return (f"{name}: {veh['distinct_complaints']} distinct NHTSA complaint IDs in {tools.derived(len(groups))} component "
                    f"groups (one complaint can name several components), data as of {asof}. Source: {url}")
        if intent == "trend":
            months = veh["monthly"][-12:]
            peak = max(months, key=lambda m: m["n_distinct"]) if months else None
            if not peak:
                return f"No monthly complaint counts for the {name}. Source: {url}"
            return (f"{name}: in the last {tools.derived(len(months))} months of data, the busiest month was {peak['month']} with "
                    f"{peak['n_distinct']} distinct complaints (data as of {asof}). Chart: {url}")
        top = ", ".join(f"{g['group']['comp_system']} ({g['group']['distinct_complaints']})" for g in groups[:3])
        return f"Most reported components for the {name}: {top}. Counts are distinct complaints, data as of {asof}. Source: {url}"
    if intent in ("recall_count", "explain_recall", "remedy"):
        veh = tools.call("recall_lookup", vehicle=v)
        if not veh:
            return f"The data service isn't answering right now. Source: {url}"
        camps = veh["recall_campaigns"]
        if intent == "recall_count":
            return (f"{name}: {tools.derived(len(camps))} recall campaigns in the cached NHTSA data (model-level, not a specific "
                    f"car). Check a specific car at https://www.nhtsa.gov/recalls. Source: {url}")
        want = re.search(r"\b(\d{2}V\d{3,6})\b", text.upper())
        camp = next((c for c in camps if want and c["campno"].startswith(want.group(1))), None) or (camps[0] if len(camps) == 1 else None)
        if camp is None:
            return f"Which campaign? The {name} has: {', '.join(c['campno'] for c in camps[:6]) or 'none in the data'}."
        ctx["campno"] = camp["campno"]
        field = "remedy" if intent == "remedy" else "summary"
        official = camp.get(field)
        if not official:
            return f"Campaign {camp['campno']} has no official {field} text in the data. Source: https://www.nhtsa.gov/recalls"
        return f"Official NHTSA text for campaign {camp['campno']} ({field}): {official[:500]}"
    return T.HELP
