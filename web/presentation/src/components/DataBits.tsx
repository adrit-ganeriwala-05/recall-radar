// Owner: C. Small shared pieces for the data-driven sections: the payload's data label and data-as-of
// date (PROJECT_SPEC §8: every screen shows both; synthetic data gets a red banner), loading/error
// states with plain wording, and date formatting that never passes calendar dates through Date().
import type { Provenance } from "@/contracts.gen";
import type { ApiFailure } from "@/data/api";
import { DESTINATIONS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

const LABEL_TEXT: Record<string, string> = {
  synthetic_fixture: "Synthetic test data",
  cached_real: "Real NHTSA records, precomputed",
  measured_evaluation: "Measured evaluation output",
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2018-04" → "Apr 2018"; anything else is shown as given. */
export function monthText(m: string | null): string {
  const match = m?.match(/^(\d{4})-(\d{2})$/);
  return match ? `${MONTHS[Number(match[2]) - 1]} ${match[1]}` : (m ?? "—");
}

/** "2018-04-01" → "Apr 1, 2018"; anything else is shown as given. */
export function dateText(d: string | null): string {
  const match = d?.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${MONTHS[Number(match[2]) - 1]} ${Number(match[3])}, ${match[1]}` : (d ?? "—");
}

export function DataLabel({ provenance }: { provenance: Provenance }) {
  const synthetic = provenance.data_label === "synthetic_fixture";
  return (
    <div className="mt-4 space-y-2">
      {synthetic && (
        <p role="note" className="rounded-md bg-[#b3261e] px-3 py-1.5 text-sm font-semibold text-white">
          SYNTHETIC TEST DATA — hand-made examples, not NHTSA records
        </p>
      )}
      <p className="text-sm text-muted">
        <span className="mr-2 rounded-full border border-line px-2 py-0.5 text-ink">{LABEL_TEXT[provenance.data_label] ?? provenance.data_label}</span>
        Data as of {provenance.data_as_of ? dateText(provenance.data_as_of) : "not applicable (test data)"}
      </p>
    </div>
  );
}

export function Loading({ what }: { what: string }) {
  return (
    <p role="status" aria-live="polite" className="mt-6 rounded-lg border border-line bg-surface px-4 py-3 text-muted">
      Loading {what}…
    </p>
  );
}

const HINT: Record<ApiFailure["kind"], string> = {
  unavailable: "This example has not been published in the current data build yet.",
  not_found: "The records for this example were not found in the current data build.",
  bad_request: "The request for this example was not accepted.",
  server: "The data service had a problem answering.",
  network: "The data service cannot be reached from this page right now.",
  timeout: "The data service took too long to answer.",
  malformed: "The data service answered with something unexpected, so nothing is shown rather than guessing.",
};

export function DataError({ error, what }: { error: ApiFailure; what: string }) {
  return (
    <div role="alert" className="mt-6 rounded-lg border border-line border-l-4 border-l-[#b3261e] bg-surface px-4 py-3">
      <p className="font-medium text-ink">{what} is not available.</p>
      <p className="mt-1 text-muted">{HINT[error.kind]}</p>
      <p className="mt-3">
        <SmartLink to={DESTINATIONS.vehicleSearch} className="inline-flex min-h-11 items-center text-cobalt underline underline-offset-4 hover:text-ink">
          Search the vehicle records in the app instead
        </SmartLink>
      </p>
    </div>
  );
}
