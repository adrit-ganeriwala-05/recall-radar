"use client";
// Owner: C. Section 3 — follow the record. The month-by-month replay already exists in the product and
// enforces the availability cutoff and later-outcome labelling; re-implementing it here would duplicate
// that logic, so this section explains it and links to the real replay. It deliberately reveals no
// outcome (no investigation or recall dates): scrolling this page is not a replay cutoff.
import { DataError, DataLabel, Loading } from "@/components/DataBits";
import { SmartLink } from "@/components/SmartLink";
import { ROUTES, SECTION_IDS } from "@/content/destinations";
import { useFeatured } from "@/data/FeaturedVehicle";
import { SectionShell } from "./SectionShell";

export function RecordSection() {
  const state = useFeatured();
  return (
    <SectionShell id={SECTION_IDS.record} title="Follow the record" chapter="record">
      <div className="mt-4 max-w-3xl space-y-4 text-lg leading-relaxed text-muted">
        <p>
          The replay steps through one vehicle and component month by month. Each month uses only the complaints that were
          public before that date.
        </p>
        <p>
          NHTSA investigations and recalls appear only after the date they became public, and they are labelled as later
          outcomes. They are never used to raise an alert.
        </p>
      </div>
      {state.status === "loading" && <Loading what="the example replay" />}
      {state.status === "error" && <DataError error={state.error} what="The example replay" />}
      {state.status === "ready" && (
        <div className="rr-card mt-8 max-w-3xl p-6 sm:p-7">
          <p className="rr-eyebrow">Published example</p>
          <p className="mt-3 text-2xl font-medium tracking-tight [overflow-wrap:anywhere]">
            {state.replay.comp_system} · {state.replay.vehicle.model_year} {state.replay.vehicle.make} {state.replay.vehicle.model}
          </p>
          <DataLabel provenance={state.replay.provenance} />
          <p className="mt-6">
            <SmartLink to={ROUTES.replay(state.replay.episode_id)} className="rr-btn rr-btn-primary min-h-11 px-5">
              Open the replay
            </SmartLink>
          </p>
        </div>
      )}
    </SectionShell>
  );
}
