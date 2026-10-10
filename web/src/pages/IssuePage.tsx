// Owner: C. C2 issue page: one vehicle + component group, its alert episodes and the evidence list.
import { Link, useParams, useSearchParams } from "react-router-dom";
import { getIssue } from "../api/client";
import { useApi } from "../api/useApi";
import { BarChart } from "../components/BarChart";
import { ProvenanceBar } from "../components/Provenance";
import { Empty, ErrorState, Loading } from "../components/States";
import type { AlertEpisode, Complaint, IssueResponse } from "../contracts.gen";
import { dateText, monthText, pct, plural, vehicleText } from "../format";
import { monthlyPoints } from "./VehiclePage";

/** The three signals are shown side by side and never combined into one number. */
export function SignalChips({ e }: { e: AlertEpisode }) {
  return (
    <ul className="chips" aria-label="Signals (shown separately, not combined)">
      <li className="chip" data-testid="chip-growth">
        <span className="chip-name">Growth</span>
        {plural(e.window_count, "distinct complaint", "distinct complaints")} in 2 months vs about{" "}
        {e.baseline_lambda.toFixed(1)} expected ({e.ratio.toFixed(1)}×)
      </li>
      <li className="chip" data-testid="chip-severity">
        <span className="chip-name">Severity (as reported in complaints)</span>
        {pct(e.severity_share)} mention a crash, fire, injury or death
      </li>
      <li className="chip" data-testid="chip-prior-action">
        <span className="chip-name">Prior NHTSA action</span>
        {e.after_official_action
          ? "A related investigation or recall was already public at the alert date"
          : "None public at the alert date"}
      </li>
    </ul>
  );
}

function Episode({ e }: { e: AlertEpisode }) {
  return (
    <article className="episode" aria-labelledby={`ep-${e.episode_id}`}>
      <h3 id={`ep-${e.episode_id}`}>
        <span aria-hidden="true">▲</span> Alert {dateText(e.alert_date)}{" "}
        <span className="small">
          (alert months {monthText(e.start_month)} to {monthText(e.end_month)})
        </span>
      </h3>
      <p>{e.explanation}</p>
      <SignalChips e={e} />
      <p className="small">
        Evidence: {plural(e.evidence_n, "complaint", "complaints")}; {pct(e.described_share)} include a description;{" "}
        {pct(e.dup_text_share)} look like repeat submissions (counted once); {pct(e.avail_fallback_share)} use an
        estimated availability date.
      </p>
      <Link className="button" to={`/replay/${encodeURIComponent(e.episode_id)}`}>
        Replay this alert month by month
      </Link>
    </article>
  );
}

function flags(c: Complaint): string[] {
  const out: string[] = [];
  if (c.crash) out.push("crash reported");
  if (c.fire) out.push("fire reported");
  if (c.injured) out.push(plural(c.injured, "injury", "injuries") + " reported");
  if (c.deaths) out.push(plural(c.deaths, "death", "deaths") + " reported");
  return out;
}

function Evidence({ c }: { c: Complaint }) {
  const f = flags(c);
  return (
    <li className="complaint" data-testid="complaint">
      <p className="complaint-head">
        <strong>Complaint {c.odino}</strong> · received {dateText(c.ldate)} · available {dateText(c.avail_date)}
        {c.avail_fallback && " (estimated)"}
        {c.faildate && <> · incident {dateText(c.faildate)}</>}
      </p>
      <p className="small">
        {c.comp_descs.join("; ")}
        {f.length > 0 && <> · {f.join(", ")}</>}
        {c.dup_text && " · probable repeat submission, counted once"}
      </p>
      <blockquote>{c.excerpt || "No description provided."}</blockquote>
      <a href={c.nhtsa_url} target="_blank" rel="noopener noreferrer" data-testid="evidence-link">
        Full complaint {c.odino} at NHTSA
      </a>
    </li>
  );
}

function Issue({
  data,
  setPage,
  episodeId,
}: {
  data: IssueResponse;
  setPage: (p: number) => void;
  episodeId: string | null;
}) {
  const { group, evidence } = data;
  const totalPages = Math.max(1, Math.ceil(evidence.total / evidence.page_size));
  return (
    <>
      <h1>
        {group.comp_system} <span className="subtle">· {vehicleText(group.vehicle)}</span>
      </h1>
      <p className="crumbs">
        <Link
          to={`/vehicle?${new URLSearchParams({
            make: group.vehicle.make,
            model: group.vehicle.model,
            year: String(group.vehicle.model_year),
          })}`}
        >
          ← All components for this vehicle
        </Link>
      </p>
      <p className="big-number">
        <strong>{plural(group.distinct_complaints, "distinct complaint", "distinct complaints")}</strong>
        {group.first_month && group.last_month && (
          <>
            {" "}
            from {monthText(group.first_month)} to {monthText(group.last_month)}
          </>
        )}
      </p>

      {data.series.length > 0 ? (
        <BarChart
          title={`Distinct ${group.comp_system} complaints per month`}
          valueLabel="Distinct complaints"
          points={monthlyPoints(data.series).map((p, i) => ({
            ...p,
            // baseline_lambda is the expected count for a 2-month window (λ̂ = 2 × typical month)
            baseline: data.series[i].baseline_lambda === null ? null : data.series[i].baseline_lambda! / 2,
            extra: [
              data.series[i].baseline_lambda?.toFixed(2) ?? "—",
              data.series[i].score?.toFixed(2) ?? "—",
            ],
          }))}
          extraHeaders={["Expected for the 2-month window", "Surprise score"]}
        />
      ) : (
        <Empty>No complaints for this component in the data range.</Empty>
      )}

      <h2>Alerts</h2>
      {data.episodes.length === 0 ? (
        <Empty>No alerts for this vehicle and component. Complaints never grew unusually fast.</Empty>
      ) : (
        data.episodes.map((e) => <Episode key={e.episode_id} e={e} />)
      )}

      <h2>Complaints</h2>
      {data.summary && (
        <section className="summary" aria-label={data.summary.label}>
          <p className="badge">{data.summary.label}</p>
          <ul>
            {data.summary.statements.map((s) => (
              <li key={s.text}>
                {s.text} <span className="small">(complaints {s.odinos.join(", ")})</span>
              </li>
            ))}
          </ul>
        </section>
      )}
      {episodeId && (
        <p className="notice" data-testid="episode-filter">
          Showing the complaints in the window of alert {episodeId}.{" "}
          <Link to={`/issue/${group.group_id}`}>Show all complaints for this component</Link>
        </p>
      )}
      <p className="small">
        Ordered by the date each complaint became available. Excerpts are redacted and shortened; follow the link
        for the full public record.
      </p>
      {evidence.items.length === 0 ? (
        <Empty>No complaints to show.</Empty>
      ) : (
        <ol className="evidence">
          {evidence.items.map((c) => (
            <Evidence key={c.odino} c={c} />
          ))}
        </ol>
      )}
      <nav className="pager" aria-label="Complaint pages">
        <button type="button" disabled={evidence.page <= 1} onClick={() => setPage(evidence.page - 1)}>
          Previous
        </button>
        <span>
          Page {evidence.page} of {totalPages} · {plural(evidence.total, "complaint", "complaints")}
        </span>
        <button type="button" disabled={evidence.next_page === null} onClick={() => setPage(evidence.next_page ?? 1)}>
          Next
        </button>
      </nav>
    </>
  );
}

export default function IssuePage() {
  const { groupId = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get("page")) || 1);
  const episodeId = params.get("episode");
  const [res, reload] = useApi(() => getIssue(groupId, page, episodeId ?? undefined), [groupId, page, episodeId]);

  return (
    <section>
      {res.state === "loading" && <Loading what="complaints" />}
      {res.state === "done" && !res.ok && <ErrorState error={res.error} retry={reload} />}
      {res.state === "done" && res.ok && (
        <>
          <ProvenanceBar provenance={res.data.provenance} source={res.source} />
          <Issue
            data={res.data}
            episodeId={episodeId}
            setPage={(p) => setParams({ ...(episodeId ? { episode: episodeId } : {}), page: String(p) })}
          />
        </>
      )}
    </section>
  );
}
