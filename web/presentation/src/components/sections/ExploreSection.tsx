"use client";
// Owner: C. Section 2 — explore a reported issue. Category buttons are the featured vehicle's real
// component groups (VehicleResponse.components, ordered by distinct complaints); choosing one changes
// the evidence panel and its links into the product (issue page, vehicle page). No symptom search
// here: F7 is not verified (ledger), and it never belongs inside the historical replay anyway.
import { useState } from "react";
import { DataError, DataLabel, Loading, monthText } from "@/components/DataBits";
import { SmartLink } from "@/components/SmartLink";
import { ROUTES, SECTION_IDS } from "@/content/destinations";
import { useFeatured } from "@/data/FeaturedVehicle";
import { SectionShell } from "./SectionShell";

const SHOWN = 6;

export function ExploreSection() {
  const state = useFeatured();
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <SectionShell id={SECTION_IDS.explore} title="Inspect the reported issue" chapter="explore">
      {state.status === "loading" && <Loading what="the example vehicle" />}
      {state.status === "error" && <DataError error={state.error} what="The example vehicle" />}
      {state.status === "ready" && (() => {
        const { vehicle } = state;
        const v = vehicle.vehicle;
        const name = `${v.model_year} ${v.make} ${v.model}`;
        const shown = vehicle.components.slice(0, SHOWN);
        const active = shown.find((c) => c.group.group_id === selected) ?? shown[0];
        return (
          <>
            <p className="mt-4 max-w-3xl text-lg leading-relaxed text-muted">
              Commonly reported problems for the {name}, the vehicle in the published example replay, grouped by component.
              Counts are distinct complaints.
            </p>
            <DataLabel provenance={vehicle.provenance} />
            {shown.length === 0 ? (
              <p className="mt-6 rounded-xl border border-line bg-surface px-4 py-3 text-muted">No complaints for this vehicle in the cached data.</p>
            ) : (
              <div className="mt-8 grid grid-cols-[repeat(auto-fit,minmax(min(100%,17rem),1fr))] gap-6">
                <div>
                  <h3 id="categories-label" className="rr-eyebrow">
                    Reported issue categories
                  </h3>
                  <ul aria-labelledby="categories-label" className="mt-4 flex flex-wrap gap-2">
                    {shown.map((c) => {
                      const on = c.group.group_id === active.group.group_id;
                      return (
                        <li key={c.group.group_id} className="min-w-0">
                          <button
                            type="button"
                            aria-pressed={on}
                            aria-controls="explore-panel"
                            onClick={() => setSelected(c.group.group_id)}
                            className={`inline-flex min-h-11 max-w-full items-center gap-2.5 rounded-full border px-4 text-left text-[15px] [overflow-wrap:anywhere] transition-colors ${on ? "border-cobalt bg-cobalt-strong text-ink shadow-[0_8px_24px_-12px_rgb(58_98_222/0.8)]" : "border-line-strong bg-surface text-ink/90 hover:border-cobalt"}`}
                          >
                            <span>{c.group.comp_system}</span>
                            <span className={`rr-figure text-[13px] ${on ? "text-ink" : "text-muted"}`}>{c.group.distinct_complaints}</span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                  {vehicle.components.length > SHOWN && (
                    <p className="mt-3 text-sm text-muted">
                      {vehicle.components.length - SHOWN} more component{vehicle.components.length - SHOWN === 1 ? "" : "s"} on the vehicle page.
                    </p>
                  )}
                </div>
                <div id="explore-panel" role="region" aria-live="polite" aria-labelledby="explore-panel-title" className="rr-card min-w-0 p-6 sm:p-7">
                  <h3 id="explore-panel-title" className="text-2xl font-medium tracking-tight [overflow-wrap:anywhere]">
                    {active.group.comp_system}
                  </h3>
                  <dl className="mt-5 grid grid-cols-1 gap-x-6 gap-y-3 border-t border-line pt-5 sm:grid-cols-[max-content_minmax(0,1fr)]">
                    <dt className="text-sm text-muted sm:pt-0.5">Distinct complaints</dt>
                    <dd data-testid="panel-count" className="rr-figure text-ink">{active.group.distinct_complaints}</dd>
                    <dt className="text-sm text-muted sm:pt-0.5">Months with complaints</dt>
                    <dd>
                      {active.group.first_month && active.group.last_month
                        ? `${monthText(active.group.first_month)} to ${monthText(active.group.last_month)}`
                        : "Not listed"}
                    </dd>
                    <dt className="text-sm text-muted sm:pt-0.5">Alerts for this component</dt>
                    <dd>
                      {active.episodes.length}
                      <span className="block text-sm text-muted">An alert means this complaint pattern deserves a closer look.</span>
                    </dd>
                  </dl>
                  <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2">
                    <SmartLink to={ROUTES.issue(active.group.group_id)} className="rr-btn rr-btn-primary min-h-11 px-5">
                      View these complaints
                    </SmartLink>
                    <SmartLink to={ROUTES.vehicle(v)} className="inline-flex min-h-11 items-center rr-link">
                      All components for this vehicle
                    </SmartLink>
                  </div>
                </div>
              </div>
            )}
          </>
        );
      })()}
    </SectionShell>
  );
}
