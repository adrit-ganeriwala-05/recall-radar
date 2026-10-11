// Owner: C. C3 replay: step month by month through what was public at each cutoff.
import { useCallback, useEffect, useState, type KeyboardEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { getHero, getReplay, getVehicle } from "../api/client";
import { useApi } from "../api/useApi";
import { BarChart } from "../components/BarChart";
import { ProvenanceBar } from "../components/Provenance";
import { RecallDrawer } from "../components/RecallDrawer";
import { features } from "../features";
import { Empty, ErrorState, Loading } from "../components/States";
import { VIN_LOOKUP_URL } from "../components/VinBox";
import type { OutcomeMatch, Replay } from "../contracts.gen";
import { dateText, heroPeriodNote, monthText, plural, statusText, vehicleText } from "../format";
import { frameMarkers, framePoints } from "../replay";

const STEP_MS = 800;

const TIER_TEXT: Record<OutcomeMatch["tier"], string> = {
  "1": "direct match",
  "2": "rule-based match",
  "3": "manual review",
  none: "no match",
};

function Outcome({ o }: { o: OutcomeMatch | null }) {
  if (!o) return <Empty>No outcome information for this alert yet.</Empty>;
  return (
    <section className="outcome" aria-labelledby="outcome-h">
      <h2 id="outcome-h">
        <span aria-hidden="true">◆</span> What NHTSA documented afterward (later reveal)
      </h2>
      <p className="small">This was not used by the detector. It is shown only to check the alert after the fact.</p>
      <dl>
        <dt>Result</dt>
        <dd data-testid="outcome-status">{statusText(o.status)}</dd>
        {o.investigation_open_date && (
          <>
            <dt>Investigation opened</dt>
            <dd>
              {dateText(o.investigation_open_date)}
              {o.earliest_action_no && <> ({o.earliest_action_no}{o.inv_type ? `, ${o.inv_type}` : ""})</>}
            </dd>
          </>
        )}
        {o.lead_days !== null && (
          <>
            <dt>Days from alert date to investigation</dt>
            <dd>{o.lead_days >= 0 ? plural(o.lead_days, "day", "days") : `${plural(-o.lead_days, "day", "days")} before the alert`}</dd>
          </>
        )}
        <dt>How it was matched</dt>
        <dd>
          {o.basis} · {TIER_TEXT[o.tier]} · confidence {o.confidence}
        </dd>
        <dt>Follow-up</dt>
        <dd>
          {o.follow_up_complete ? "Complete" : "Not finished"} (through {dateText(o.follow_up_end)})
        </dd>
        {o.recall_campnos.length > 0 && (
          <>
            <dt>Related recall campaigns (model-level)</dt>
            <dd>
              {o.recall_campnos.join(", ")}. These apply to the model and model year, not to any specific car.{" "}
              <a href={VIN_LOOKUP_URL} target="_blank" rel="noopener noreferrer" data-testid="vin-link">
                Check a VIN at NHTSA
              </a>
            </dd>
          </>
        )}
      </dl>
    </section>
  );
}

export function ReplayView({ data }: { data: Replay }) {
  const frames = data.frames;
  const last = frames.length - 1;
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  // PRD v2 F3: recall markers with campno/link open the F1 card; hidden until their date unless toggled
  const linked = features.recallMarkers && data.markers.some((m) => m.type === "recall_reported" && m.campno && m.link);
  const [showLater, setShowLater] = useState(false);
  const [drawer, setDrawer] = useState<{ campno: string; link: "issue" | "vehicle" | null; el: Element } | null>(null);
  const [veh] = useApi(
    linked && drawer ? () => getVehicle(data.vehicle.make, data.vehicle.model, data.vehicle.model_year) : null,
    [linked && drawer !== null],
  );
  const closeDrawer = useCallback(() => {
    const el = drawer?.el as HTMLElement | SVGElement | undefined;
    setDrawer(null);
    setTimeout(() => el?.focus(), 0);
  }, [drawer]);

  useEffect(() => {
    if (!playing) return;
    if (index >= last) {
      setPlaying(false);
      return;
    }
    const t = setTimeout(() => setIndex((i) => Math.min(last, i + 1)), STEP_MS);
    return () => clearTimeout(t);
  }, [playing, index, last]);

  if (frames.length === 0) return <Empty>This replay has no months to show.</Empty>;
  const frame = frames[index];
  const go = (i: number) => {
    setPlaying(false);
    setIndex(Math.max(0, Math.min(last, i)));
  };
  const onKey = (e: KeyboardEvent) => {
    if ((e.target as HTMLElement).tagName === "INPUT") return; // the slider handles its own keys
    const keys: Record<string, () => void> = {
      ArrowLeft: () => go(index - 1),
      ArrowRight: () => go(index + 1),
      Home: () => go(0),
      End: () => go(last),
    };
    if (keys[e.key]) {
      e.preventDefault();
      keys[e.key]();
    }
  };

  return (
    <>
      <h1>
        Replay {data.episode_id} <span className="subtle">· {data.comp_system} · {vehicleText(data.vehicle)}</span>
      </h1>
      <p className="replay-banner">{data.banner}</p>

      <div className="replay-controls" role="group" aria-label="Replay controls" onKeyDown={onKey}>
        <button type="button" aria-label="Restart" onClick={() => go(0)}>
          ⏮ Restart
        </button>
        <button type="button" aria-label="Step back" onClick={() => go(index - 1)} disabled={index === 0}>
          ◀ Step back
        </button>
        <button
          type="button"
          onClick={() => {
            if (index >= last) setIndex(0);
            setPlaying((p) => !p);
          }}
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? "⏸ Pause" : "▶ Play"}
        </button>
        <button type="button" aria-label="Step forward" onClick={() => go(index + 1)} disabled={index === last}>
          Step forward ▶
        </button>
        <button type="button" aria-label="Jump to end" onClick={() => go(last)} disabled={index === last}>
          Jump to end ⏭
        </button>
        <label className="slider">
          <span className="visually-hidden">Replay month</span>
          <input
            type="range"
            min={0}
            max={last}
            value={index}
            aria-valuetext={`Data through ${monthText(frame.month)}`}
            onChange={(e) => go(Number(e.target.value))}
          />
        </label>
      </div>

      <p className="frame-status" role="status" aria-live="polite" data-testid="frame-status">
        Using complaints available before {dateText(frame.cutoff)}: {monthText(frame.month)} had{" "}
        {plural(frame.n_distinct, "distinct complaint", "distinct complaints")}
        {frame.partial && " (partial month)"}
        {frame.baseline_lambda !== null && <>, about {frame.baseline_lambda.toFixed(1)} expected for the 2-month window</>}
        {frame.score !== null && <>, surprise score {frame.score.toFixed(2)}</>}.{" "}
        {frame.alert_active ? <strong>▲ Alert active.</strong> : "No alert."}
      </p>

      {linked && (
        <label className="small later-toggle">
          <input type="checkbox" checked={showLater} onChange={(e) => setShowLater(e.target.checked)} /> Show later outcomes
          (recall campaigns reported after the current replay date)
        </label>
      )}
      {drawer && (
        <RecallDrawer
          campno={drawer.campno}
          link={drawer.link}
          campaign={veh.state === "done" && veh.ok ? veh.data.recall_campaigns.find((c) => c.campno === drawer.campno) : undefined}
          loading={veh.state === "loading"}
          vehicle={data.vehicle}
          dataAsOf={veh.state === "done" && veh.ok ? veh.data.provenance.data_as_of : null}
          onClose={closeDrawer}
        />
      )}
      <BarChart
        title="Distinct complaints per month, as known at the replay date"
        valueLabel="Distinct complaints"
        points={framePoints(frames, index)}
        markers={frameMarkers(frames, data.markers, index, linked ? { showLater, onRecall: (campno, el) => setDrawer({ campno, el, link: data.markers.find((m) => m.campno === campno)?.link ?? null }) } : {})}
        extraHeaders={["Expected (2-month window)", "Surprise score"]}
      />
      <p className="small">
        ▲ marks the alert the method raised from complaints public at that date. ◆ marks investigations and recalls,
        which are later reveals and never inputs to the alert.
      </p>

      {index === last ? (
        <Outcome o={data.outcome} />
      ) : (
        <p>
          <button type="button" className="link-button" onClick={() => go(last)}>
            Skip to the end to see what NHTSA documented afterward
          </button>
        </p>
      )}
      <p>
        <Link to={`/issue/${data.group_id}?${new URLSearchParams({ episode: data.episode_id })}`}>
          See the complaints behind this alert
        </Link>
      </p>
    </>
  );
}

export default function ReplayPage() {
  const { episodeId = "" } = useParams();
  const [res, reload] = useApi(() => getReplay(episodeId), [episodeId]);
  const [hero] = useApi(getHero, []);
  // The hero replay says which period it comes from (B's frozen rule may fall back to development).
  const heroPeriod = hero.state === "done" && hero.ok && hero.data.episode_id === episodeId ? hero.data.period : null;
  return (
    <section>
      {res.state === "loading" && <Loading what="replay" />}
      {res.state === "done" && !res.ok && <ErrorState error={res.error} retry={reload} />}
      {res.state === "done" && res.ok && (
        <>
          <ProvenanceBar provenance={res.data.provenance} source={res.source} />
          {heroPeriod && (
            <p className="notice" data-testid="hero-period">
              {heroPeriodNote(heroPeriod)}
            </p>
          )}
          <ReplayView key={res.data.episode_id} data={res.data} />
        </>
      )}
    </section>
  );
}
