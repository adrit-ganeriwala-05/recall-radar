// Owner: C. PRD v2 F7 "Describe the problem": browser-only search over the vehicle's symptom index.
// The typed text stays in this component: it is never sent, stored, logged or put in the URL.
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getSymptomIndex } from "../api/client";
import { useApi } from "../api/useApi";
import type { VehicleKey } from "../contracts.gen";
import { dateText } from "../format";
import { search } from "../search/symptoms";

export const EXAMPLES = ["door doesn't lock properly", "brakes make noise", "steering wheel shakes", "engine stalls while driving"];
export const METHOD_LINE = "Text and phrase search in the current cached snapshot. A match is not a diagnosis.";
export const NO_MATCH = "No similar complaints found in this dataset with this search method.";
const SHOWN = 20;

export function SymptomSearch({ vehicle, reportHref }: { vehicle: VehicleKey; reportHref: string }) {
  const [idx] = useApi(() => getSymptomIndex(vehicle.make, vehicle.model, vehicle.model_year), [
    vehicle.make, vehicle.model, vehicle.model_year,
  ]);
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setQuery(text), 250);
    return () => clearTimeout(t);
  }, [text]);

  const data = idx.state === "done" && idx.ok ? idx.data : null;
  const hits = useMemo(() => (data && query.trim() ? search(query, data.docs, data) : []), [data, query]);
  if (idx.state === "done" && !idx.ok) return null; // no index for this vehicle/database: the feature hides itself
  const labels = new Map((data?.concepts ?? []).map((c) => [c.id, c.label]));

  return (
    <section className="symptom-search" aria-labelledby="symptom-h" data-testid="symptom-search">
      <h2 id="symptom-h">Describe the problem</h2>
      <label htmlFor="symptom-input" className="visually-hidden">
        Describe the problem in your own words
      </label>
      <div className="symptom-input-row">
        <input
          id="symptom-input"
          type="search"
          autoComplete="off"
          spellCheck
          placeholder={`e.g. ${EXAMPLES[1]}`}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={!data}
        />
        {text && (
          <button type="button" onClick={() => { setText(""); setQuery(""); }}>
            Clear
          </button>
        )}
      </div>
      <p className="chips" aria-label="Examples">
        {EXAMPLES.map((ex) => (
          <button key={ex} type="button" className="chip" onClick={() => setText(ex)} disabled={!data}>
            {ex}
          </button>
        ))}
      </p>
      {idx.state === "loading" && <p className="state">Loading this vehicle's complaint texts…</p>}
      {data && query.trim() && (
        <>
          <h3>Similar reported symptoms</h3>
          <p className="small" data-testid="symptom-method">{METHOD_LINE}</p>
          <p role="status" aria-live="polite" data-testid="symptom-count">
            {hits.length === 0 ? "" : hits.length > SHOWN ? `${hits.length} similar complaints; showing the newest ${SHOWN}.` : `${hits.length} similar complaint${hits.length === 1 ? "" : "s"}.`}
          </p>
          {hits.length === 0 ? (
            <p className="state state-empty" data-testid="symptom-none">
              {NO_MATCH} <Link to={reportHref}>Report a problem</Link>
            </p>
          ) : (
            <ol className="symptom-results">
              {hits.slice(0, SHOWN).map((h) => {
                const d = data.docs[h.docIndex];
                return (
                  <li key={d.odino} data-testid="symptom-hit">
                    <p className="small">
                      <a href={d.nhtsa_url} target="_blank" rel="noopener noreferrer">Complaint {d.odino}</a> · available{" "}
                      {dateText(d.avail_date)} ·{" "}
                      {h.conceptIds.length ? h.conceptIds.map((c) => labels.get(c) ?? c).join(", ") : "words in your description"}
                      {h.matchedTerms.length > 0 && <> · matched: {h.matchedTerms.join(", ")}</>}
                      {d.group_id && <> · <Link to={`/issue/${d.group_id}`}>issue page</Link></>}
                    </p>
                    <blockquote className="excerpt">{d.excerpt}</blockquote>
                  </li>
                );
              })}
            </ol>
          )}
        </>
      )}
    </section>
  );
}
