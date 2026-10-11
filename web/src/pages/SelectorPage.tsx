// Owner: C. C1: make -> model -> year selector, plus the hero replay entry point.
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getHero, getMakes, getModels, getYears } from "../api/client";
import { useApi } from "../api/useApi";
import { ProvenanceBar } from "../components/Provenance";
import { ErrorState, Loading } from "../components/States";
import { heroPeriodNote, PROMISE } from "../format";

export default function SelectorPage() {
  const navigate = useNavigate();
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");
  const [makes, reloadMakes] = useApi(getMakes, []);
  const [models] = useApi(make ? () => getModels(make) : null, [make]);
  const [years] = useApi(make && model ? () => getYears(make, model) : null, [make, model]);
  const [hero] = useApi(getHero, []);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!make || !model || !year) return;
    navigate(`/vehicle?${new URLSearchParams({ make, model, year })}`);
  };

  const options = (l: typeof makes) => (l.state === "done" && l.ok ? (l.data.items as (string | number)[]) : []);

  return (
    <section>
      <h1>Find a vehicle</h1>
      <p className="lede promise" data-testid="promise">
        {PROMISE}
      </p>
      <section className="what-alert" aria-labelledby="what-alert-h">
        <h2 id="what-alert-h">What an alert means</h2>
        <p data-testid="reframe">
          Use Recall Radar to read a vehicle&apos;s full complaint history and to see what was public before each
          NHTSA investigation. Whether alerts came earlier for investigated vehicles than for comparable ones is
          measured against chance on the <Link to="/results">Results</Link> page.
        </p>
        <p>
          An alert means complaints about one vehicle and one component grew much faster than that vehicle and
          component usually see. It means the pattern deserves a closer look. It is not a defect finding, not a recall
          forecast, and not a claim that anyone noticed it before NHTSA staff did. Counts are distinct complaints.
        </p>
      </section>

      {makes.state === "loading" && <Loading what="makes" />}
      {makes.state === "done" && !makes.ok && <ErrorState error={makes.error} retry={reloadMakes} />}
      {makes.state === "done" && makes.ok && (
        <>
          <ProvenanceBar provenance={makes.data.provenance} source={makes.source} />
          <form className="selector" onSubmit={submit} aria-label="Vehicle selector">
            <div className="field">
              <label htmlFor="sel-make">Make</label>
              <select
                id="sel-make"
                value={make}
                onChange={(e) => {
                  setMake(e.target.value);
                  setModel("");
                  setYear("");
                }}
              >
                <option value="">Choose a make</option>
                {options(makes).map((m) => (
                  <option key={m}>{m}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="sel-model">Model</label>
              <select
                id="sel-model"
                value={model}
                disabled={!make || models.state !== "done"}
                onChange={(e) => {
                  setModel(e.target.value);
                  setYear("");
                }}
              >
                <option value="">{make ? "Choose a model" : "Choose a make first"}</option>
                {make &&
                  options(models).map((m) => (
                    <option key={m}>{m}</option>
                  ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="sel-year">Year</label>
              <select id="sel-year" value={year} disabled={!model || years.state !== "done"} onChange={(e) => setYear(e.target.value)}>
                <option value="">{model ? "Choose a year" : "Choose a model first"}</option>
                {model &&
                  options(years).map((y) => (
                    <option key={y}>{y}</option>
                  ))}
              </select>
            </div>
            <button type="submit" disabled={!make || !model || !year}>
              Show vehicle
            </button>
          </form>
          {make && models.state === "done" && models.ok && options(models).length === 0 && (
            <p className="state state-empty">No models with complaints for this make in the data range.</p>
          )}
          {make && models.state === "done" && !models.ok && <ErrorState error={models.error} />}
          {model && years.state === "done" && !years.ok && <ErrorState error={years.error} />}
        </>
      )}

      {hero.state === "done" && hero.ok && (
        <aside className="hero-card">
          <h2>See an example replay</h2>
          <p>Step through one complaint pattern month by month, using only what was public at each date.</p>
          <Link className="button" to={`/replay/${encodeURIComponent(hero.data.episode_id)}`}>
            Open replay {hero.data.episode_id}
          </Link>
          <p className="small" data-testid="hero-period">
            {heroPeriodNote(hero.data.period)}
          </p>
          {hero.data.provenance.data_label === "synthetic_fixture" && (
            <p className="small">This example is built from made-up test records, not real complaints.</p>
          )}
        </aside>
      )}
    </section>
  );
}
