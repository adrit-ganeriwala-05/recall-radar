"""F8 (PRD_v2 §4): what goes on the one-page buyer report, as one pure selection function.

`select_report_data(con, make, model, model_year)` reads the cached tables and returns the
report's content. It applies a fixed, stated rule; it does not rank by anything but counts and
dates, and it computes no score. The same vehicle and database always give the same result.

Counting rules are the ones `/api/vehicle` uses, so the numbers agree:
- distinct complaints: distinct complaint ids (`complaint_doc`, one row per id) for the vehicle;
- issue groups: distinct complaint ids per component system (`complaint_row`);
- recall campaigns: `recall_campaign` rows for the make, model and model year, one per campno.
Investigations are the NHTSA actions whose vehicle list names the make, model and model year
(`inv_vehicle`), one per action number.

The caller passes the make and model as they are stored (the API resolves aliases first).
Nothing here is imported by the detector, the matcher or the evaluation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

MAX_ISSUE_GROUPS = 5
MAX_INVESTIGATIONS = 5
MAX_CAMPAIGNS = 6
COUNT_BASIS = "distinct NHTSA complaint IDs"
SELECTION_RULE = (
    f"Shown: up to {MAX_ISSUE_GROUPS} component systems with the most distinct complaints for this make, model and "
    f"model year (ties in alphabetical order); up to {MAX_INVESTIGATIONS} NHTSA investigations that name this vehicle, "
    f"newest opening date first; up to {MAX_CAMPAIGNS} recall campaigns that name this vehicle, newest report date first. "
    "Nothing is ranked by severity, and no score is calculated."
)


@dataclass(frozen=True)
class IssueGroupLine:
    comp_system: str
    distinct_complaints: int
    first_month: str  # YYYY-MM, month the first complaint became available
    last_month: str


@dataclass(frozen=True)
class InvestigationLine:
    action_no: str
    inv_type: str
    open_date: date | None
    subject: str | None


@dataclass(frozen=True)
class CampaignLine:
    campno: str
    component: str
    report_date: date | None


@dataclass(frozen=True)
class ReportSelection:
    make: str
    model: str
    model_year: int
    distinct_complaints: int
    count_basis: str
    complaint_date_first: date | None  # earliest and latest date NHTSA received a complaint (LDATE)
    complaint_date_last: date | None
    issue_groups: tuple[IssueGroupLine, ...]
    issue_groups_total: int
    investigations: tuple[InvestigationLine, ...]
    investigations_total: int
    campaigns: tuple[CampaignLine, ...]
    campaigns_total: int
    selection_rule: str

    def showing(self, name: str) -> str:
        """'showing n of m' for one of the three lists."""
        return f"showing {len(getattr(self, name))} of {getattr(self, name + '_total')}"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _date(value: Any) -> date | None:
    if value is None:
        return None
    return value.date() if hasattr(value, "date") else value


def _has(con: Any, table: str) -> bool:
    return bool(con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [table]).fetchone()[0])


def select_report_data(con: Any, make: str, model: str, model_year: int) -> ReportSelection:
    key = [make, model, int(model_year)]
    n, first, last = con.execute(
        "SELECT count(DISTINCT odino), min(CAST(ldate AS DATE)), max(CAST(ldate AS DATE)) FROM complaint_doc "
        "WHERE make = ? AND model = ? AND model_year = ?", key,
    ).fetchone()  # fmt: skip

    groups = con.execute(
        """SELECT comp_system, count(DISTINCT odino) AS n, strftime(min(avail_date), '%Y-%m'), strftime(max(avail_date), '%Y-%m')
           FROM complaint_row WHERE make = ? AND model = ? AND model_year = ?
           GROUP BY 1 ORDER BY n DESC, comp_system ASC""",
        key,
    ).fetchall()

    investigations: list[tuple] = []
    if _has(con, "inv_vehicle") and _has(con, "inv_action"):
        investigations = con.execute(
            """SELECT a.action_no, a.inv_type, CAST(a.odate AS DATE), a.subject
               FROM inv_action a
               WHERE a.action_no IN (SELECT DISTINCT action_no FROM inv_vehicle WHERE make = ? AND model = ? AND model_year = ?)
               ORDER BY a.odate DESC NULLS LAST, a.action_no ASC""",
            key,
        ).fetchall()

    campaigns: list[tuple] = []
    if _has(con, "recall_campaign"):
        campaigns = con.execute(
            """SELECT CAST(campno AS VARCHAR) AS campno, min(component), min(CAST(report_date AS DATE)) AS reported
               FROM recall_campaign WHERE make = ? AND model = ? AND model_year = ?
               GROUP BY 1 ORDER BY reported DESC NULLS LAST, campno ASC""",
            key,
        ).fetchall()

    return ReportSelection(
        make=make, model=model, model_year=int(model_year),
        distinct_complaints=int(n or 0), count_basis=COUNT_BASIS,
        complaint_date_first=_date(first), complaint_date_last=_date(last),
        issue_groups=tuple(IssueGroupLine(s, int(c), a, b) for s, c, a, b in groups[:MAX_ISSUE_GROUPS]),
        issue_groups_total=len(groups),
        investigations=tuple(InvestigationLine(a, str(t), _date(o), s) for a, t, o, s in investigations[:MAX_INVESTIGATIONS]),
        investigations_total=len(investigations),
        campaigns=tuple(CampaignLine(c, comp, _date(d)) for c, comp, d in campaigns[:MAX_CAMPAIGNS]),
        campaigns_total=len(campaigns),
        selection_rule=SELECTION_RULE,
    )  # fmt: skip
