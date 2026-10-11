// Owner: D. F8 one-page buyer report (PRD_v2 §4 F8). Renders only `ReportData` from GET /api/report
// (B's selection, A's API). No VIN, no draft text, no score, no comparative wording. Official NHTSA
// text is shown verbatim. Printed with the browser: "Print / Save as PDF" (US Letter, one page).
import type { ReportData } from "../../contracts.gen";
import { dateText, plural, vehicleText } from "../../format";
import "./buyer-report.css";

export const REPORT_TITLE = "Used-car complaint and recall summary";
export const VIN_LOOKUP = "https://www.nhtsa.gov/recalls";

function day(d: string | null | undefined): string {
  return d ? dateText(d.slice(0, 10)) : "not stated";
}

function firstLine(text: string | null | undefined): string | null {
  const line = (text ?? "").split(/\r?\n/).find((l) => l.trim() !== "");
  return line ? line.trim() : null;
}

function absolute(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  return typeof window === "undefined" ? path : new URL(path, window.location.origin).toString();
}

export function vehiclePageHref(d: ReportData): string {
  const v = d.vehicle;
  return `/vehicle?${new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year) }).toString()}`;
}

function Showing({ n, m, href, what }: { n: number; m: number; href: string; what: string }) {
  return (
    <p className="br-showing">
      Showing {n} of {m} {what}.{" "}
      {m > n && <a href={absolute(href)}>See all on the vehicle page</a>}
    </p>
  );
}

export function BuyerReport({ data, generated }: { data: ReportData; generated: Date }) {
  const vp = vehiclePageHref(data);
  const totalInv = data.total_investigations ?? data.investigations.length;
  const totalCamp = data.total_campaigns ?? data.campaigns.length;
  const snapshot = data.snapshot_date ?? data.provenance.data_as_of;
  return (
    <article className="br" data-testid="buyer-report">
      <header className="br-head">
        <h1>{REPORT_TITLE}</h1>
        <p className="br-vehicle">{vehicleText(data.vehicle)}</p>
        <dl className="br-meta">
          <div>
            <dt>Complaints covered</dt>
            <dd>
              {day(data.complaint_date_range.start)} – {day(data.complaint_date_range.end)}
            </dd>
          </div>
          <div>
            <dt>Data snapshot</dt>
            <dd>
              {snapshot ? day(snapshot) : "not stated"}
              {data.provenance.snapshot_id && <span className="br-small"> ({data.provenance.snapshot_id})</span>}
            </dd>
          </div>
          <div>
            <dt>Generated</dt>
            <dd>{dateText(generated.toISOString().slice(0, 10))}</dd>
          </div>
          <div>
            <dt>Complaints</dt>
            <dd>
              {plural(data.distinct_complaints, "complaint", "complaints")}{" "}
              <span className="br-small">({data.counting_basis ?? "distinct NHTSA complaint IDs"})</span>
            </dd>
          </div>
        </dl>
      </header>

      <section>
        <h2>Most reported components</h2>
        {data.top_groups.length === 0 ? (
          <p>No complaints for this vehicle in this dataset.</p>
        ) : (
          <ol className="br-list">
            {data.top_groups.map((g) => (
              <li key={g.group.group_id}>
                <a href={absolute(g.link)}>{g.group.comp_system}</a> —{" "}
                {plural(g.distinct_complaints, "complaint", "complaints")}
              </li>
            ))}
          </ol>
        )}
        <Showing n={data.shown_n} m={data.total_groups} href={vp} what="component groups" />
      </section>

      <section>
        <h2>NHTSA investigations</h2>
        {data.investigations.length === 0 ? (
          <p>No NHTSA investigations for this vehicle in this dataset.</p>
        ) : (
          <ul className="br-list">
            {data.investigations.map((i) => (
              <li key={i.action_no}>
                <a href={absolute(i.link)}>
                  {i.action_no} ({i.inv_type})
                </a>
                , opened {day(i.open_date)}
                {i.subject && <span className="br-clip br-remedy">{i.subject}</span>}
              </li>
            ))}
          </ul>
        )}
        <Showing n={data.investigations.length} m={totalInv} href={vp} what="investigations" />
      </section>

      <section>
        <h2>Recall campaigns for this model</h2>
        {data.campaigns.length === 0 ? (
          <p>No matching recalls in this cached dataset. This doesn&apos;t mean a specific car has no open recall — check by VIN.</p>
        ) : (
          <ul className="br-list">
            {data.campaigns.map((c) => {
              const remedy = firstLine(c.remedy);
              return (
                <li key={c.campno}>
                  <a href={c.source_url ?? VIN_LOOKUP}>{c.campno}</a> · {c.component} · reported {day(c.report_date)}
                  {remedy && (
                    <span className="br-clip br-remedy">
                      Remedy (official NHTSA text): {remedy}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
        <Showing n={data.campaigns.length} m={totalCamp} href={vp} what="recall campaigns" />
      </section>

      <footer className="br-foot">
        <p className="br-small">Selection: {data.selection_rule}</p>
        <p className="br-small">
          What this covers: complaints filed with NHTSA, NHTSA investigations and recall campaigns for this make,
          model and year, from public NHTSA data. What it does not cover: any specific car&apos;s history, repairs or
          whether its recalls were completed. Check a specific car by VIN at{" "}
          <a href={data.vin_lookup_url ?? VIN_LOOKUP}>{data.vin_lookup_url ?? VIN_LOOKUP}</a>. Full vehicle page:{" "}
          <a href={absolute(vp)}>{absolute(vp)}</a>
        </p>
      </footer>
    </article>
  );
}

export default BuyerReport;
