"""Recall Radar contracts v1 — the single source of truth for shared data shapes.

Owner: A (data/backend).  Reviewers: B (detector/evaluation shapes), C (API shapes).
Derived artifacts (never edit by hand):
  contracts/schema/recall_radar.schema.json   <- scripts/export_contracts.py
  web/src/contracts.gen.ts                    <- `npm --prefix web run gen:contracts`
Change protocol: docs/CONTRACTS.md, section "Change protocol".

Conventions (also in docs/CONTRACTS.md):
  * Calendar dates are ISO `YYYY-MM-DD` with no time zone (NHTSA publishes dates only).
  * Months are `YYYY-MM` strings.
  * Timestamps (`generated_at`) are UTC ISO 8601.
  * Counts are DISTINCT complaints (distinct ODINO), never "owners".
  * A field typed `X | None` is always present in JSON; `null` means "not applicable or
    not yet known" and the description says which.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

CONTRACT_VERSION = "1.1.0"

MonthStr = str  # pattern enforced per field: ^\d{4}-(0[1-9]|1[0-2])$
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class Contract(BaseModel):
    """Base: unknown fields are rejected so drift is caught early."""

    model_config = ConfigDict(extra="forbid", frozen=True)


# --------------------------------------------------------------------------- enums


class DataLabel(StrEnum):
    """Every payload says what kind of data it carries. The UI must show this label."""

    synthetic_fixture = "synthetic_fixture"  # hand-made test data; never real numbers
    cached_real = "cached_real"  # real NHTSA records, precomputed, not an evaluation result
    measured_evaluation = "measured_evaluation"  # output of evaluate.py on a frozen config


class AvailabilityBasis(StrEnum):
    datea = "DATEA"  # date added to the NHTSA file (primary proxy)
    ldate_plus_7 = "LDATE_PLUS_7"  # received date + 7 days (labeled experiment / fallback)


class OutcomeStatus(StrEnum):
    early = "early"  # 60 <= lead_days <= 730
    late = "late"  # 0 <= lead_days < 60
    after_official_action = "after_official_action"  # lead_days < 0
    outside_window = "outside_window"  # lead_days > 730
    unmatched = "unmatched"  # follow-up complete, no related investigation found
    ambiguous = "ambiguous"  # candidate(s) exist but manual review said "unsure"
    follow_up_incomplete = "follow_up_incomplete"  # < follow_up_days elapsed, nothing yet


class MatchTier(StrEnum):
    direct = "1"
    rule_based = "2"
    manual = "3"
    none = "none"


class Confidence(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class InvType(StrEnum):
    PE = "PE"  # Preliminary Evaluation
    EA = "EA"  # Engineering Analysis
    DP = "DP"  # Defect Petition
    RQ = "RQ"  # Recall Query
    AQ = "AQ"  # Audit Query
    OTHER = "OTHER"


class Period(StrEnum):
    development = "development"
    held_out = "held_out"


class MetricStatus(StrEnum):
    measured = "measured"
    pending = "pending"
    not_applicable = "not_applicable"


class ErrorCode(StrEnum):
    invalid_parameter = "invalid_parameter"  # HTTP 400
    not_found = "not_found"  # HTTP 404
    unavailable = "unavailable"  # HTTP 503 (data file missing / not yet built)
    internal = "internal"  # HTTP 500


# --------------------------------------------------------------------------- shared


class Provenance(Contract):
    contract_version: str = Field(default=CONTRACT_VERSION)
    data_label: DataLabel
    snapshot_id: str | None = Field(
        description="source_snapshot id (sha256 prefix of SNAPSHOT.lock.json); null only for synthetic fixtures"
    )
    data_as_of: date | None = Field(
        description="Latest NHTSA 'Updated' date among source files in the snapshot; null for fixtures"
    )
    config_hash: str | None = Field(description="12-hex hash of config.yaml; null for fixtures")
    git_sha: str | None = Field(description="Commit that produced the payload; null for fixtures")
    availability_basis: AvailabilityBasis | None
    generated_at: datetime

    @model_validator(mode="after")
    def _real_data_needs_provenance(self) -> Provenance:
        if self.data_label != DataLabel.synthetic_fixture:
            missing = [
                n
                for n in ("snapshot_id", "data_as_of", "config_hash", "git_sha", "availability_basis")
                if getattr(self, n) is None
            ]
            if missing:
                raise ValueError(f"{self.data_label.value} payload missing provenance: {missing}")
        return self


class VehicleKey(Contract):
    make: str = Field(min_length=1, description="Uppercase, trimmed, single-spaced NHTSA make")
    model: str = Field(min_length=1, description="Uppercase, trimmed, single-spaced; alias table applied")
    model_year: int = Field(ge=1949, le=2030, description="Unknown model year (9999) never appears here")


class Complaint(Contract):
    """One distinct complaint (ODINO) as shown in the evidence list. Never one per component row."""

    odino: str = Field(pattern=r"^\d+$")
    vehicle: VehicleKey
    comp_systems: list[str] = Field(description="Distinct top-level systems, sorted ascending")
    comp_descs: list[str] = Field(description="Distinct full COMPDESC values, sorted ascending")
    ldate: date = Field(description="Received by NHTSA (LDATE)")
    datea: date | None = Field(description="Added to file (DATEA) as parsed; null if invalid")
    avail_date: date = Field(description="Availability proxy used everywhere (see CONTRACTS.md)")
    avail_fallback: bool = Field(description="True when avail_date = LDATE + 7 days")
    faildate: date | None = Field(description="Incident date; display only; null if missing/invalid")
    crash: bool | None
    fire: bool | None
    injured: int | None = Field(ge=0)
    deaths: int | None = Field(ge=0)
    dup_text: bool = Field(description="Probable repeat submission; counted once in its group")
    excerpt: str = Field(max_length=400, description="Redacted CDESCR, at most 400 characters")
    nhtsa_url: str = Field(description="https://api.nhtsa.gov/complaints/odinumber?odinumber=<ODINO>")


class IssueGroup(Contract):
    group_id: str = Field(pattern=r"^g_[0-9a-f]{12}$")
    vehicle: VehicleKey
    comp_system: str
    sub_issue: str | None = Field(description="Always null in P0; P1 semantic sub-issue label")
    distinct_complaints: int = Field(ge=0)
    first_month: MonthStr | None = Field(pattern=MONTH_PATTERN)
    last_month: MonthStr | None = Field(pattern=MONTH_PATTERN)


class MonthlyPoint(Contract):
    month: MonthStr = Field(pattern=MONTH_PATTERN)
    n_distinct: int = Field(ge=0)
    baseline_lambda: float | None = Field(
        description="Expected count for the 2-month window ending this month; null if not scored"
    )
    score: float | None = Field(description="S = -log10 P(Y >= c); null if not scored")
    alert: bool
    partial: bool = Field(description="Month incomplete at the data cutoff; never scored")


class AlertEpisode(Contract):
    episode_id: str = Field(pattern=r"^E-[0-9A-Za-z]+$")
    group_id: str = Field(pattern=r"^g_[0-9a-f]{12}$")
    vehicle: VehicleKey
    comp_system: str
    sub_issue: str | None
    start_month: MonthStr = Field(pattern=MONTH_PATTERN)
    end_month: MonthStr = Field(pattern=MONTH_PATTERN)
    alert_date: date = Field(description="First day after the first alert month ends")
    peak_score: float = Field(ge=0, description="Max S over the episode's alert months")
    window_count: int = Field(ge=0, description="c of the FIRST alert month's 2-month window")
    baseline_lambda: float = Field(gt=0, description="Expected count for that same window")
    ratio: float = Field(ge=0, description="window_count / baseline_lambda")
    severity_share: float = Field(ge=0, le=1, description="Owner-reported crash/fire/injury/death share")
    evidence_n: int = Field(ge=0)
    described_share: float = Field(ge=0, le=1)
    dup_text_share: float = Field(ge=0, le=1)
    avail_fallback_share: float = Field(ge=0, le=1)
    after_official_action: bool = Field(
        description="A related investigation/recall was already public before alert_date"
    )
    explanation: str = Field(description="One plain sentence built from the numbers above")
    config_hash: str


class OutcomeMatch(Contract):
    """Post-hoc link from an alert episode to a documented outcome. Never a detector input."""

    episode_id: str = Field(pattern=r"^E-[0-9A-Za-z]+$")
    family_id: str | None
    earliest_action_no: str | None
    inv_type: InvType | None
    investigation_open_date: date | None = Field(description="Earliest ODATE in the family")
    tier: MatchTier
    basis: str = Field(description="Human-readable matching evidence")
    confidence: Confidence
    lead_days: int | None = Field(description="investigation_open_date - alert_date; + means alert first")
    status: OutcomeStatus
    recall_campnos: list[str] = Field(description="Distinct campaign numbers, sorted; may be empty")
    follow_up_end: date
    follow_up_complete: bool
    reviewer: str | None = Field(description="Worker letter for tier 3 manual labels")

    @model_validator(mode="after")
    def _status_consistent(self) -> OutcomeMatch:
        s = self.status
        if s in (OutcomeStatus.unmatched, OutcomeStatus.follow_up_incomplete):
            if self.tier != MatchTier.none or self.lead_days is not None:
                raise ValueError(f"{s.value} requires tier 'none' and lead_days null")
        if s in (
            OutcomeStatus.early,
            OutcomeStatus.late,
            OutcomeStatus.after_official_action,
            OutcomeStatus.outside_window,
        ):
            if self.lead_days is None or self.investigation_open_date is None:
                raise ValueError(f"{s.value} requires lead_days and investigation_open_date")
            d = self.lead_days
            ok = {
                OutcomeStatus.early: 60 <= d <= 730,
                OutcomeStatus.late: 0 <= d < 60,
                OutcomeStatus.after_official_action: d < 0,
                OutcomeStatus.outside_window: d > 730,
            }[s]
            if not ok:
                raise ValueError(f"lead_days {d} inconsistent with status {s.value}")
        if s == OutcomeStatus.unmatched and not self.follow_up_complete:
            raise ValueError("unmatched requires follow_up_complete; use follow_up_incomplete")
        return self


class ReplayFrame(Contract):
    """Knowledge as of the START of `cutoff`: only complaints with avail_date < cutoff are used.

    Monthly frames use cutoff = first day of the month after `month`, so `month` is complete.
    """

    cutoff: date = Field(description="Exclusive bound: avail_date < cutoff. Monthly frame: first day of next month")
    month: MonthStr = Field(pattern=MONTH_PATTERN)
    n_distinct: int = Field(ge=0)
    baseline_lambda: float | None
    score: float | None
    partial: bool
    alert_active: bool = Field(
        description="`month` is an alert month of an episode whose alert_date <= cutoff (data < cutoff only)"
    )


class ReplayMarker(Contract):
    type: Literal["alert", "investigation_opened", "recall_reported"]
    date: date
    label: str
    is_outcome: bool = Field(
        description="True for investigation/recall markers: a later reveal, never detector input"
    )
    action_no: str | None
    match_tier: MatchTier | None
    lead_days: int | None
    # 1.1.0 (F3): recall_reported markers only; null on every other marker type
    campno: str | None = Field(default=None, description="NHTSA campaign of a recall_reported marker")
    link: Literal["issue", "vehicle"] | None = Field(
        default=None,
        description="issue: campaign of the episode's matched investigation family; "
        "vehicle: other campaign for the same make/model/year ('Other recall for this model')",
    )


class Replay(Contract):
    provenance: Provenance
    episode_id: str = Field(pattern=r"^E-[0-9A-Za-z]+$")
    group_id: str = Field(pattern=r"^g_[0-9a-f]{12}$")
    vehicle: VehicleKey
    comp_system: str
    frames: list[ReplayFrame] = Field(description="Ascending by month, contiguous")
    markers: list[ReplayMarker] = Field(description="Ascending by date")
    outcome: OutcomeMatch | None
    banner: str

    @model_validator(mode="after")
    def _ordered(self) -> Replay:
        months = [f.month for f in self.frames]
        if months != sorted(months) or len(set(months)) != len(months):
            raise ValueError("frames must be strictly ascending by month")
        dates = [m.date for m in self.markers]
        if dates != sorted(dates):
            raise ValueError("markers must be ascending by date")
        return self


class Metric(Contract):
    name: Literal[
        "eligible_families",
        "excluded_families",
        "early_coverage_all",
        "early_coverage_sample",
        "chance_coverage",
        "median_lead_days",
        "lead_days_q1",
        "lead_days_q3",
        "episodes_per_month",
        "top25_matched",
        "top25_unmatched",
        "top25_ambiguous",
        "ingestion_retained_share",
        "pipeline_runtime_s",
    ]
    status: MetricStatus
    value: float | None
    ci_low: float | None
    ci_high: float | None
    numerator: int | None
    denominator: int | None
    note: str | None

    @model_validator(mode="after")
    def _no_invented_numbers(self) -> Metric:
        if self.status != MetricStatus.measured and any(
            v is not None for v in (self.value, self.ci_low, self.ci_high, self.numerator, self.denominator)
        ):
            raise ValueError(f"metric {self.name} is {self.status.value}: all numeric fields must be null")
        if self.status == MetricStatus.measured and self.value is None:
            raise ValueError(f"metric {self.name} is measured but value is null")
        return self


class EvalCase(Contract):
    family_id: str
    earliest_action_no: str
    inv_type: InvType
    vehicles: list[VehicleKey]
    comp_system: str
    investigation_open_date: date
    eligible: bool
    exclusion_reason: str | None
    in_sample: bool
    best_episode_id: str | None
    status: OutcomeStatus | Literal["missed", "excluded"]
    lead_days: int | None
    match_tier: MatchTier
    review_label: Literal["related", "not_related", "unsure"] | None


class AuditRow(Contract):
    rank: int = Field(ge=1)
    episode_id: str
    vehicle: VehicleKey
    comp_system: str
    peak_score: float
    alert_date: date
    outcome: OutcomeMatch


class ExclusionCount(Contract):
    reason: str
    n: int = Field(ge=0)


class EvaluationSummary(Contract):
    provenance: Provenance
    run_id: str
    period: Period
    seed: int
    freeze_tag: str | None = Field(description="Git tag of the frozen config; required for held_out")
    metrics: list[Metric]
    cases: list[EvalCase] = Field(description="Every eligible and excluded family, sorted by family_id")
    audit: list[AuditRow] = Field(description="held_out only: top-K alerts by peak score; else empty")
    exclusions: list[ExclusionCount]

    @model_validator(mode="after")
    def _rules(self) -> EvaluationSummary:
        if (
            self.provenance.data_label == DataLabel.measured_evaluation
            and self.period == Period.held_out
            and not self.freeze_tag
        ):
            raise ValueError("held_out results require freeze_tag")
        if self.provenance.data_label == DataLabel.cached_real:
            raise ValueError("evaluation summaries are measured_evaluation or synthetic_fixture")
        names = [m.name for m in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("duplicate metric names")
        return self


# --------------------------------------------------------------------------- API envelopes

T = TypeVar("T")


class Page(Contract, Generic[T]):
    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    next_page: int | None


class MetaResponse(Contract):
    provenance: Provenance
    mode: Literal["cached", "fixture"]
    complaint_received_range: tuple[date, date] | None
    periods: dict[str, tuple[date, date]]


class ListResponse(Contract):
    provenance: Provenance
    items: list[str] | list[int] = Field(description="Sorted ascending; years as integers")


class VehicleComponent(Contract):
    group: IssueGroup
    episodes: list[AlertEpisode] = Field(description="Ascending by alert_date")


EXPLANATION_SOURCE_FIELDS = ("summary", "consequence", "remedy")


class ExplanationSentence(Contract):
    """One plain-language sentence (F2). Every claim must be traceable to the official text."""

    text: str = Field(min_length=1)
    source_fields: list[Literal["summary", "consequence", "remedy"]] = Field(min_length=1)
    source_spans: list[str] = Field(min_length=1, description="Verbatim substrings of the cited official fields")

    @model_validator(mode="after")
    def _short(self) -> ExplanationSentence:
        if len(self.text.split()) > 45:
            raise ValueError("an explanation sentence has at most 45 words")
        return self


class RecallExplanation(Contract):
    """F2. `fallback` = show the official text only (never labeled AI); it carries no sentences."""

    status: Literal["accepted", "fallback"]
    sentences: list[ExplanationSentence] = Field(default_factory=list, max_length=2)
    model: str | None = None
    prompt_version: str | None = None

    @model_validator(mode="after")
    def _status_matches(self) -> RecallExplanation:
        if self.status == "fallback" and self.sentences:
            raise ValueError("a fallback explanation carries no sentences")
        if self.status == "accepted" and not (self.sentences and self.model and self.prompt_version):
            raise ValueError("an accepted explanation needs sentences, model and prompt_version")
        return self


class RecallCampaign(Contract):
    campno: str
    component: str
    report_date: date | None
    # 1.1.0 (F1): official NHTSA text verbatim; null when the source lacks the field
    summary: str | None = None
    consequence: str | None = None
    remedy: str | None = None
    park_it: StrictBool | None = Field(default=None, description="Do-not-drive flag; null = unknown (never shown)")
    park_outside: StrictBool | None = Field(default=None, description="Park-outside flag; null = unknown (never shown)")
    report_date_basis: str | None = Field(default=None, description="Which source date `report_date` is")
    source_url: str | None = None
    snapshot_id: str | None = None
    explanation: RecallExplanation | None = None


class VehicleResponse(Contract):
    provenance: Provenance
    vehicle: VehicleKey
    distinct_complaints: int = Field(ge=0, description="Distinct ODINO for the vehicle, all systems")
    components: list[VehicleComponent] = Field(description="Descending by distinct_complaints, then comp_system")
    monthly: list[MonthlyPoint] = Field(description="Vehicle-level distinct complaints per month, ascending")
    recall_campaigns: list[RecallCampaign] = Field(description="Model-level, deduplicated by campno")
    vin_lookup_url: Literal["https://www.nhtsa.gov/recalls"] = "https://www.nhtsa.gov/recalls"
    note: str


class SummaryStatement(Contract):
    text: str = Field(description="No digits; no banned words; validated before storage")
    odinos: list[str] = Field(min_length=1, description="Cited complaints; each must be in the evidence set")


class IssueSummary(Contract):
    """P1-2 only. Always null in P0. Shown under the label below, above the raw excerpts."""

    label: Literal["AI summary of owner descriptions; read the complaints below"]
    statements: list[SummaryStatement] = Field(min_length=2, max_length=4)
    model: str
    prompt_version: str


class IssueResponse(Contract):
    provenance: Provenance
    group: IssueGroup
    series: list[MonthlyPoint]
    episodes: list[AlertEpisode]
    evidence: Page[Complaint] = Field(description="Ordered by avail_date asc, then odino asc")
    summary: IssueSummary | None = Field(description="P1-2; null unless a validated summary exists")


# --------------------------------------------------------------------------- 1.1.0: F7 symptom search


class SymptomDoc(Contract):
    odino: str = Field(pattern=r"^\d+$")
    comp_systems: list[str]
    avail_date: date
    excerpt: str = Field(max_length=400, description="Redacted at ingest and again at serving time")
    group_id: str | None = Field(default=None, pattern=r"^g_[0-9a-f]{12}$")
    nhtsa_url: str


class SymptomAlias(Contract):
    phrase: str = Field(min_length=1)
    concepts: list[str] = Field(min_length=1)


class SymptomConcept(Contract):
    id: str = Field(min_length=1)
    label: str
    comp_systems: list[str]
    terms: list[str]


class SymptomIndex(Contract):
    """GET /api/symptom-index: searched in the browser; the query never reaches the server."""

    provenance: Provenance
    vehicle: VehicleKey
    snapshot_label: Literal["current cached snapshot"] = "current cached snapshot"
    docs: list[SymptomDoc] = Field(max_length=2000, description="Newest first (avail_date desc, then odino desc)")
    aliases: list[SymptomAlias]
    concepts: list[SymptomConcept]

    @model_validator(mode="after")
    def _newest_first(self) -> SymptomIndex:
        keys = [(d.avail_date, int(d.odino)) for d in self.docs]
        if keys != sorted(keys, reverse=True):
            raise ValueError("docs must be newest first")
        return self


# --------------------------------------------------------------------------- 1.1.0: F8 buyer report


class DateRange(Contract):
    start: date | None
    end: date | None


class ReportGroup(Contract):
    group: IssueGroup
    distinct_complaints: int = Field(ge=0)
    link: str = Field(description="App path of the issue page")


class ReportInvestigation(Contract):
    action_no: str
    inv_type: InvType
    open_date: date
    subject: str | None
    link: str


class ReportData(Contract):
    """GET /api/report: data for the one-page buyer report; counts equal /api/vehicle."""

    provenance: Provenance
    vehicle: VehicleKey
    complaint_date_range: DateRange
    snapshot_date: date | None
    distinct_complaints: int = Field(ge=0)
    counting_basis: Literal["distinct NHTSA complaint IDs"] = "distinct NHTSA complaint IDs"
    top_groups: list[ReportGroup] = Field(max_length=5)
    shown_n: int = Field(ge=0, description="len(top_groups)")
    total_groups: int = Field(ge=0)
    investigations: list[ReportInvestigation] = Field(max_length=5)
    total_investigations: int = Field(default=0, ge=0)
    campaigns: list[RecallCampaign] = Field(max_length=6)
    total_campaigns: int = Field(default=0, ge=0)
    vin_lookup_url: Literal["https://www.nhtsa.gov/recalls"] = "https://www.nhtsa.gov/recalls"
    selection_rule: str

    @model_validator(mode="after")
    def _counts(self) -> ReportData:
        if self.shown_n != len(self.top_groups) or self.total_groups < self.shown_n:
            raise ValueError("shown_n must equal len(top_groups) and not exceed total_groups")
        if self.total_investigations < len(self.investigations) or self.total_campaigns < len(self.campaigns):
            raise ValueError("a total is smaller than the list it summarises")
        return self


class ErrorBody(Contract):
    code: ErrorCode
    message: str
    detail: dict[str, str] | None


class ErrorResponse(Contract):
    error: ErrorBody


class HeroPointer(Contract):
    """exports/demo/hero.json — which replay the pitch uses and why."""

    provenance: Provenance
    episode_id: str
    period: Period
    rule: str
    rule_commit: str = Field(description="Commit that froze the rule; must predate the held-out run")


# Exported (in this order) to contracts/schema/recall_radar.schema.json
EXPORTED_MODELS: list[type[BaseModel]] = [
    Provenance,
    VehicleKey,
    Complaint,
    IssueGroup,
    MonthlyPoint,
    AlertEpisode,
    OutcomeMatch,
    ReplayFrame,
    ReplayMarker,
    Replay,
    Metric,
    EvalCase,
    AuditRow,
    ExclusionCount,
    EvaluationSummary,
    MetaResponse,
    ListResponse,
    VehicleComponent,
    RecallCampaign,
    VehicleResponse,
    IssueResponse,
    SummaryStatement,
    IssueSummary,
    ErrorBody,
    ErrorResponse,
    ExplanationSentence,
    RecallExplanation,
    SymptomDoc,
    SymptomAlias,
    SymptomConcept,
    SymptomIndex,
    DateRange,
    ReportGroup,
    ReportInvestigation,
    ReportData,
    HeroPointer,
]
