// Owner: C. PRD v2 F1: one official recall card per campno; reused by the F3 replay drawer.
// Official NHTSA text is shown verbatim as plain text (React escapes it; CSS keeps line breaks).
import { useState } from "react";
import type { RecallCampaign, VehicleKey } from "../contracts.gen";
import { features } from "../features";
import { dateText, vehicleText } from "../format";
import { VIN_LOOKUP_URL } from "./VinBox";

export const NO_RECALLS_TEXT =
  "No matching recalls in this cached dataset. This doesn't mean a specific car has no open recall — check by VIN.";
export const AI_LABEL = "Plain-language explanation (AI-generated — check the official text)";
const LONG = 700; // characters across the three official fields before the card offers "Show full text"

function OfficialRow({ label, text, full }: { label: string; text: string | null | undefined; full: boolean }) {
  if (!text) return null; // missing fields are omitted, never shown as empty
  const shown = full || text.length <= LONG / 2 ? text : `${text.slice(0, LONG / 2).trimEnd()}…`;
  return (
    <div className="official-row">
      <dt>{label}</dt>
      <dd className="official-text">{shown}</dd>
    </div>
  );
}

export function RecallCard({
  campaign: c,
  vehicle,
  dataAsOf,
}: {
  campaign: RecallCampaign;
  vehicle: VehicleKey;
  dataAsOf?: string | null;
}) {
  const total = (c.summary?.length ?? 0) + (c.consequence?.length ?? 0) + (c.remedy?.length ?? 0);
  const long = total > LONG;
  const [full, setFull] = useState(!long);
  const exp = c.explanation;
  const accepted = features.recallExplain && exp?.status === "accepted" && (exp.sentences?.length ?? 0) > 0;
  const id = `recall-${c.campno}`;
  return (
    <article className="recall-card" aria-labelledby={`${id}-h`} data-testid="recall-card">
      <h3 id={`${id}-h`}>
        NHTSA campaign {c.campno} <span className="subtle">· {c.component}</span>
      </h3>
      {c.park_it === true && (
        <p className="recall-banner banner-do-not-drive" role="alert" data-testid="banner-park-it">
          Do not drive — NHTSA campaign {c.campno}
        </p>
      )}
      {c.park_outside === true && (
        <p className="recall-banner banner-park-outside" role="alert" data-testid="banner-park-outside">
          Park outside — NHTSA campaign {c.campno}
        </p>
      )}
      {accepted && (
        <section className="recall-explain" data-testid="recall-explanation">
          <h4>{AI_LABEL}</h4>
          {exp!.sentences!.map((s, i) => (
            <p key={i}>{s.text}</p>
          ))}
        </section>
      )}
      {(c.summary || c.consequence || c.remedy) && (
        <section className="official" data-testid="official-text">
          <h4>Official NHTSA text</h4>
          <dl>
            <OfficialRow label="Summary" text={c.summary} full={full} />
            <OfficialRow label="Consequence" text={c.consequence} full={full} />
            <OfficialRow label="Remedy" text={c.remedy} full={full} />
          </dl>
          {long && (
            <button type="button" className="link-button" aria-expanded={full} onClick={() => setFull((f) => !f)}>
              {full ? "Show less" : "Show full official text"}
            </button>
          )}
        </section>
      )}
      <p className="small">
        {c.report_date ? (
          <>
            Reported {dateText(c.report_date)}
            {c.report_date_basis && <> ({c.report_date_basis})</>}
          </>
        ) : (
          "Report date not in the data"
        )}
        {c.source_url && (
          <>
            {" · "}
            <a href={c.source_url} target="_blank" rel="noopener noreferrer">
              Source: NHTSA recalls
            </a>
          </>
        )}
        {(dataAsOf || c.snapshot_id) && (
          <>
            {" · "}
            {dataAsOf && <>Data as of {dateText(dataAsOf)}</>}
            {c.snapshot_id && <> (snapshot {c.snapshot_id})</>}
          </>
        )}
      </p>
      <p className="recall-vin" data-testid="recall-vin">
        This campaign covers the {vehicleText(vehicle)} you selected.{" "}
        <a href={VIN_LOOKUP_URL} target="_blank" rel="noopener noreferrer">
          Check a specific car by VIN →
        </a>
      </p>
    </article>
  );
}

export function RecallCards({
  campaigns,
  vehicle,
  dataAsOf,
}: {
  campaigns: RecallCampaign[];
  vehicle: VehicleKey;
  dataAsOf?: string | null;
}) {
  // one card per campno even if a payload ever repeats one (PRD F1.1)
  const seen = new Set<string>();
  const unique = campaigns.filter((c) => !seen.has(c.campno) && seen.add(c.campno));
  if (unique.length === 0) return <p className="state state-empty">{NO_RECALLS_TEXT}</p>;
  return (
    <div className="recall-cards">
      {unique.map((c) => (
        <RecallCard key={c.campno} campaign={c} vehicle={vehicle} dataAsOf={dataAsOf} />
      ))}
    </div>
  );
}
