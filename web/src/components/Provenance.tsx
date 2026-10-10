// Owner: C. Every screen shows its data label and data-as-of date; synthetic data gets a red banner.
import type { Provenance } from "../contracts.gen";
import type { Source } from "../api/client";
import { DATA_LABEL_TEXT, dateText } from "../format";

export function SyntheticBanner({ provenance }: { provenance: Provenance }) {
  if (provenance.data_label !== "synthetic_fixture") return null;
  return (
    <div className="synthetic-banner" role="alert">
      SYNTHETIC TEST DATA — hand-made examples, not NHTSA records
    </div>
  );
}

export function ProvenanceBar({ provenance, source }: { provenance: Provenance; source?: Source }) {
  return (
    <>
      <SyntheticBanner provenance={provenance} />
      <p className="provenance" data-testid="provenance">
        <span className={`badge badge-${provenance.data_label}`}>{DATA_LABEL_TEXT[provenance.data_label]}</span>
        <span>
          Data as of {provenance.data_as_of ? dateText(provenance.data_as_of) : "not applicable (test data)"}
        </span>
        {source === "offline" && <span className="badge badge-offline">Offline demo data</span>}
        {provenance.availability_basis === "LDATE_PLUS_7" && (
          <span className="badge badge-offline">Received-date experiment: availability = received date + 7 days</span>
        )}
      </p>
    </>
  );
}
