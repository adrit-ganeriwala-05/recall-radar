// Owner: C. C4 results. Every number here is read from the evaluation JSON (exports/demo via the
// API, or the bundled offline copy). Pending metrics say so; nothing is filled in by the UI.
import { useState, type KeyboardEvent, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getResults, resultsCsvUrl, type Period, type Source } from "../api/client";
import { useApi } from "../api/useApi";
import { ProvenanceBar } from "../components/Provenance";
import { Empty, ErrorState, Loading } from "../components/States";
import type { AuditRow, EvalCase, EvaluationSummary, Metric } from "../contracts.gen";
import {
  HELD_OUT_NOT_RUN,
  METRICS,
  dateText,
  metricCiText,
  metricFractionText,
  metricValueText,
  statusText,
  vehicleText,
} from "../format";

const PERIODS: { id: Period; label: string }[] = [
  { id: "development", label: "Development period" },
  { id: "held_out", label: "Held-out period" },
];

export function MetricCard({ m }: { m: Metric }) {
  const def = METRICS[m.name];
  const ci = metricCiText(m);
  const frac = metricFractionText(m);
  return (
    <div className={`metric metric-${m.status}`} data-testid={`metric-${m.name}`}>
      <p className="metric-label">{def.label}</p>
      <p className="metric-value" data-testid="metric-value">
        {metricValueText(m)}
      </p>
      {frac && <p className="metric-detail">{frac}</p>}
      {ci && <p className="metric-detail">{ci}</p>}
      <p className="metric-help">{def.help}</p>
      {m.note && <p className="metric-note">{m.note}</p>}
    </div>
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
              <td>{c.vehicles.length ? c.vehicles.map(vehicleText).join("; ") : "Several makes"}</td>
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
  const allPending = data.metrics.every((m) => m.status === "pending");
  const metrics = [
    ...FIRST.flatMap((n) => data.metrics.filter((m) => m.name === n)),
    ...data.metrics.filter((m) => !FIRST.includes(m.name)),
  ];
  const csv = source ? resultsCsvUrl(data.period, source) : null;
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
      <div className="metric-grid">
        {metrics.map((m) => (
          <MetricCard key={m.name} m={m} />
        ))}
      </div>

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

export default function ResultsPage() {
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
      <div role="tablist" aria-label="Evaluation period" className="tabs" onKeyDown={onKey}>
        {PERIODS.map((p) => (
          <button
            key={p.id}
            id={`tab-${p.id}`}
            type="button"
            role="tab"
            aria-selected={period === p.id}
            aria-controls={`panel-${p.id}`}
            tabIndex={period === p.id ? 0 : -1}
            onClick={() => choose(p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${period}`} aria-labelledby={`tab-${period}`}>
        <PeriodResults key={period} period={period} />
      </div>
    </section>
  );
}
