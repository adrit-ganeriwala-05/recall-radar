// Owner: C. C4 results. Every number here is read from the evaluation JSON (exports/demo via the
// API, or the bundled offline copy). Pending metrics say so; nothing is filled in by the UI.
import { motion } from "motion/react";
import { useMemo, useState, type KeyboardEvent, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getResults, resultsCsvUrl, type Period, type Source } from "../api/client";
import { useApi } from "../api/useApi";
import { ChartFrame, CoverageComparison, LeadTimeScatter, type ChartState } from "../charts";
import { coverageRow, earlyLeadPoints, fractionText, type CoverageRow } from "../charts/data";
import { ProvenanceBar } from "../components/Provenance";
import { Empty, ErrorState, Loading } from "../components/States";
import type { AuditRow, EvalCase, EvaluationSummary, Metric } from "../contracts.gen";
import {
  HELD_OUT_NOT_RUN,
  METRICS,
  coverageVerdict,
  dateText,
  metricCiText,
  metricFractionText,
  metricValueText,
  periodNote,
  statusText,
  vehicleText,
} from "../format";
import { issueForHref } from "./IssueForPage";
import { sectionViewport, useMotionPresets } from "../ui/motion";

const PERIODS: { id: Period; label: string }[] = [
  { id: "development", label: "Development period" },
  { id: "held_out", label: "Held-out period" },
];

export function MetricCard({ m }: { m: Metric }) {
  const mp = useMotionPresets();
  const def = METRICS[m.name];
  const ci = metricCiText(m);
  const frac = metricFractionText(m);
  return (
    <motion.div className={`metric metric-${m.status}`} data-testid={`metric-${m.name}`} variants={mp.sectionChild} {...mp.cardHover}>
      <p className="metric-label">{def.label}</p>
      <p className="metric-value" data-testid="metric-value">
        {metricValueText(m)}
      </p>
      {frac && <p className="metric-detail">{frac}</p>}
      {ci && <p className="metric-detail">{ci}</p>}
      <p className="metric-help">{def.help}</p>
      {m.note && <p className="metric-note">{m.note}</p>}
    </motion.div>
  );
}

function CaseTable({ cases }: { cases: EvalCase[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th scope="col">Investigation</th>
            <th scope="col">Opened</th>
            <th scope="col">Vehicles</th>
            <th scope="col">Component</th>
            <th scope="col">Result</th>
            <th scope="col">Lead days</th>
            <th scope="col">Alert</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c.family_id} data-testid="case-row">
              <th scope="row">
                {c.earliest_action_no} <span className="small">({c.inv_type}, {c.family_id})</span>
              </th>
              <td>{dateText(c.investigation_open_date)}</td>
              <td>
                {c.vehicles.length
                  ? c.vehicles.map((v, i) => (
                      <span key={vehicleText(v)}>
                        {i > 0 && "; "}
                        <Link to={issueForHref(v, c.comp_system)} title={`Monthly counts: ${vehicleText(v)}, ${c.comp_system}`}>
                          {vehicleText(v)}
                        </Link>
                      </span>
                    ))
                  : "Several makes"}
              </td>
              <td>{c.comp_system}</td>
              <td>
                {statusText(c.status)}
                {c.exclusion_reason && <> ({c.exclusion_reason})</>}
                {c.review_label && <span className="small"> · reviewer: {c.review_label.replace("_", " ")}</span>}
              </td>
              <td>{c.lead_days ?? "—"}</td>
              <td>
                {c.best_episode_id ? (
                  <Link to={`/replay/${encodeURIComponent(c.best_episode_id)}`}>{c.best_episode_id}</Link>
                ) : (
                  "—"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AuditTable({ rows }: { rows: AuditRow[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th scope="col">Rank</th>
            <th scope="col">Alert</th>
            <th scope="col">Vehicle</th>
            <th scope="col">Component</th>
            <th scope="col">Peak score</th>
            <th scope="col">Alert date</th>
            <th scope="col">Result</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.episode_id} data-testid="audit-row">
              <td>{r.rank}</td>
              <th scope="row">
                <Link to={`/replay/${encodeURIComponent(r.episode_id)}`}>{r.episode_id}</Link>
              </th>
              <td>{vehicleText(r.vehicle)}</td>
              <td>{r.comp_system}</td>
              <td>{r.peak_score.toFixed(2)}</td>
              <td>{dateText(r.alert_date)}</td>
              <td>{statusText(r.outcome.status)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Lead times: one point per matched early alert in the results file (Bklit scatter), exact values. */
export function LeadTimeChart({ cases }: { cases: EvalCase[] }) {
  const points = useMemo(() => earlyLeadPoints(cases), [cases]);
  const title = "Days from alert to investigation, matched early alerts";
  const state: ChartState = points.length === 0 ? { kind: "empty", message: "No matched early alerts with a lead time in this results file yet." } : { kind: "ready" };
  return (
    <ChartFrame
      title={title}
      description="Each point is one investigation that an alert preceded within the accepted early-alert interval, placed at its exact lead time in days. The dashed lines mark the interval's edges."
      state={state}
      table={
        <table data-testid="lead-table">
          <caption className="visually-hidden">{title}</caption>
          <thead>
            <tr>
              <th scope="col">Investigation family</th>
              <th scope="col">Earliest action</th>
              <th scope="col">Lead days</th>
            </tr>
          </thead>
          <tbody>
            {points.map((pt) => (
              <tr key={pt.familyId} data-testid="lead-row">
                <th scope="row">{pt.familyId}</th>
                <td>{pt.actionNo ?? "—"}</td>
                <td>{pt.leadDays}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
      summary={<>{points.length === 1 ? "One matched early alert" : `${points.length} matched early alerts`}: {points.map((pt) => `${pt.leadDays} days`).join(", ")}.</>}
      testId="lead-time"
    >
      <LeadTimeScatter title={title} points={points} />
    </ChartFrame>
  );
}

function Group({ title, n, open, children, testId }: { title: string; n: number; open: boolean; children: ReactNode; testId: string }) {
  return (
    <details open={open} className="case-group" data-testid={testId}>
      <summary>
        {title} ({n})
      </summary>
      {n === 0 ? <Empty>None.</Empty> : children}
    </details>
  );
}

// Coverage sits beside chance coverage; the rest keep the payload order.
const FIRST: Metric["name"][] = ["early_coverage_all", "chance_coverage"];

export function Results({ data, source }: { data: EvaluationSummary; source?: Source }) {
  const mp = useMotionPresets();
  const allPending = data.metrics.every((m) => m.status === "pending");
  const metrics = [
    ...FIRST.flatMap((n) => data.metrics.filter((m) => m.name === n)),
    ...data.metrics.filter((m) => !FIRST.includes(m.name)),
  ];
  const csv = source ? resultsCsvUrl(data.period, source) : null;
  const verdict = coverageVerdict(
    data.metrics.find((m) => m.name === "early_coverage_all"),
    data.metrics.find((m) => m.name === "chance_coverage"),
  );
  const prov = data.provenance;
  const by = (s: EvalCase["status"]) => data.cases.filter((c) => c.status === s);
  const missed = by("missed");
  const unmatchedCases = by("unmatched");
  const ambiguousCases = by("ambiguous");
  const unmatchedAudit = data.audit.filter((r) => r.outcome.status === "unmatched");
  const ambiguousAudit = data.audit.filter((r) => r.outcome.status === "ambiguous");
  const matched = data.cases.filter((c) => !["missed", "unmatched", "ambiguous", "excluded"].includes(c.status));
  const excluded = by("excluded");

  return (
    <>
      {data.period === "held_out" && allPending && (
        <p className="notice" data-testid="held-out-not-run">
          {HELD_OUT_NOT_RUN}
        </p>
      )}
      {periodNote(data.period, data.freeze_tag) && (
        <p className="notice" data-testid="period-note">
          {periodNote(data.period, data.freeze_tag)}
        </p>
      )}
      {verdict && (
        <p className="verdict" data-testid="coverage-verdict">
          {verdict}
        </p>
      )}
      <p className="small" data-testid="run-info">
        Run {data.run_id}
        {data.freeze_tag && <> · thresholds frozen at {data.freeze_tag}</>}
        {prov.config_hash && <> · config hash {prov.config_hash}</>}
        {prov.git_sha && <> · git SHA {prov.git_sha}</>}
        {prov.snapshot_id && <> · snapshot {prov.snapshot_id}</>}
        {csv && (
          <>
            {" "}
            ·{" "}
            <a href={csv} download data-testid="results-csv">
              Download results CSV
            </a>
          </>
        )}
      </p>

      <h2>Metrics</h2>
      <motion.div className="metric-grid" variants={mp.section} initial="hidden" whileInView="shown" viewport={sectionViewport}>
        {metrics.map((m) => (
          <MetricCard key={m.name} m={m} />
        ))}
      </motion.div>

      <h2>Lead time</h2>
      <LeadTimeChart cases={data.cases} />

      <h2>Cases</h2>
      <p className="small">
        Misses, unmatched alerts and unclear matches are listed first and open by default, so the limits are as
        visible as the hits.
      </p>
      <Group title="Investigations with no earlier alert (misses)" n={missed.length} open testId="misses-list">
        <CaseTable cases={missed} />
      </Group>
      <Group
        title="Alerts with no related investigation documented (unmatched)"
        n={unmatchedCases.length + unmatchedAudit.length}
        open
        testId="group-unmatched"
      >
        {unmatchedCases.length > 0 && <CaseTable cases={unmatchedCases} />}
        {unmatchedAudit.length > 0 && <AuditTable rows={unmatchedAudit} />}
      </Group>
      <Group
        title="Unclear matches (ambiguous)"
        n={ambiguousCases.length + ambiguousAudit.length}
        open
        testId="group-ambiguous"
      >
        {ambiguousCases.length > 0 && <CaseTable cases={ambiguousCases} />}
        {ambiguousAudit.length > 0 && <AuditTable rows={ambiguousAudit} />}
      </Group>
      <Group title="Investigations with an alert before them" n={matched.length} open={false} testId="group-matched">
        <CaseTable cases={matched} />
      </Group>
      {data.audit.length > 0 && (
        <Group title="Top alerts by peak score (audit)" n={data.audit.length} open={false} testId="group-audit">
          <AuditTable rows={data.audit} />
        </Group>
      )}
      <Group title="Excluded from scoring" n={excluded.length} open={false} testId="group-excluded">
        {data.exclusions.length > 0 && (
          <table>
            <thead>
              <tr>
                <th scope="col">Reason</th>
                <th scope="col">Investigations</th>
              </tr>
            </thead>
            <tbody>
              {data.exclusions.map((x) => (
                <tr key={x.reason}>
                  <th scope="row">{x.reason}</th>
                  <td>{x.n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <CaseTable cases={excluded} />
      </Group>
    </>
  );
}

function PeriodResults({ period }: { period: Period }) {
  const [res, reload] = useApi(() => getResults(period), [period]);
  if (res.state !== "done") return <Loading what="results" />;
  if (!res.ok) {
    if (period === "held_out" && (res.error.error.code === "not_found" || res.error.error.code === "unavailable")) {
      return (
        <p className="notice" data-testid="held-out-not-run">
          {HELD_OUT_NOT_RUN}
        </p>
      );
    }
    return <ErrorState error={res.error} retry={reload} />;
  }
  return (
    <>
      <ProvenanceBar provenance={res.data.provenance} source={res.source} />
      <Results data={res.data} source={res.source} />
    </>
  );
}

/** Measured coverage beside chance coverage, development and held-out as separate groups. */
export function CoverageSection() {
  const [dev, reloadDev] = useApi(() => getResults("development"), []);
  const [held] = useApi(() => getResults("held_out"), []);
  const title = "Early-alert coverage beside chance coverage, by period";
  const rows = useMemo<CoverageRow[]>(
    () => [
      coverageRow("development", "Development period", dev.state === "done" && dev.ok ? dev.data.metrics : null),
      coverageRow("held_out", "Held-out period", held.state === "done" && held.ok ? held.data.metrics : null),
    ],
    [dev, held],
  );
  const pendingText = (r: CoverageRow): string | null => {
    if (r.recallRadarFraction || r.chanceFraction) return null;
    if (r.period === "held_out") {
      if (held.state === "done" && !held.ok && held.error.error.code !== "not_found" && held.error.error.code !== "unavailable") return "Held-out results could not be loaded.";
      return HELD_OUT_NOT_RUN;
    }
    return "Not measured in this results file.";
  };
  let state: ChartState = { kind: "ready" };
  if (dev.state !== "done" || held.state !== "done") state = { kind: "loading" };
  else if (!dev.ok) state = { kind: "error", message: `Development results could not be loaded: ${dev.error.error.message}`, onRetry: reloadDev };
  else if (rows.every((r) => !r.recallRadarFraction && !r.chanceFraction)) state = { kind: "empty", message: "No measured coverage values in the cached results yet." };
  const line = (r: CoverageRow) =>
    r.recallRadarFraction || r.chanceFraction
      ? `${r.label}: early-alert coverage ${r.recallRadarFraction ? fractionText(r.recallRadarFraction) : "not measured"}, chance coverage ${r.chanceFraction ? fractionText(r.chanceFraction) : "not measured"}.`
      : `${r.label}: ${pendingText(r)}`;
  return (
    <ChartFrame
      title={title}
      description="For each period on its own: the share of documented investigations that an alert preceded, beside the share expected from randomly timed alerts. Each value is a count of investigations over the eligible total."
      state={state}
      table={
        <table data-testid="coverage-table">
          <caption className="visually-hidden">{title}</caption>
          <thead>
            <tr>
              <th scope="col">Period</th>
              <th scope="col">Early-alert coverage</th>
              <th scope="col">Chance coverage</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.period} data-testid={`coverage-row-${r.period}`}>
                <th scope="row">{r.label}</th>
                <td>{r.recallRadarFraction ? fractionText(r.recallRadarFraction) : pendingText(r) ?? "Not measured"}</td>
                <td>{r.chanceFraction ? fractionText(r.chanceFraction) : pendingText(r) ?? "Not measured"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
      summary={rows.map(line).join(" ")}
      testId="coverage-chart"
    >
      <CoverageComparison title={title} rows={rows} pendingText={pendingText} />
    </ChartFrame>
  );
}

export default function ResultsPage() {
  const mp = useMotionPresets();
  const [params, setParams] = useSearchParams();
  const initial = params.get("period") === "held_out" ? "held_out" : "development";
  const [period, setPeriod] = useState<Period>(initial);
  const choose = (p: Period) => {
    setPeriod(p);
    setParams({ period: p }, { replace: true });
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      const next = period === "development" ? "held_out" : "development";
      choose(next);
      document.getElementById(`tab-${next}`)?.focus();
    }
  };
  return (
    <section>
      <h1>Results</h1>
      <p className="lede">
        How often a documented NHTSA investigation was preceded by an alert for the same vehicle and component, compared
        with randomly timed alerts. Development results were used to choose settings; held-out results were computed
        once, after the settings were frozen.
      </p>
      <CoverageSection />
      <div role="tablist" aria-label="Evaluation period" className="tabs" onKeyDown={onKey}>
        {PERIODS.map((p) => (
          <motion.button
            key={p.id}
            id={`tab-${p.id}`}
            type="button"
            role="tab"
            aria-selected={period === p.id}
            aria-controls={`panel-${p.id}`}
            tabIndex={period === p.id ? 0 : -1}
            onClick={() => choose(p.id)}
            className="rr-tab"
            {...mp.buttonTap}
          >
            {p.label}
            {period === p.id && <motion.span className="rr-tab-indicator" layoutId="results-tab-indicator" aria-hidden="true" />}
          </motion.button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${period}`} aria-labelledby={`tab-${period}`}>
        <PeriodResults key={period} period={period} />
      </div>
    </section>
  );
}
