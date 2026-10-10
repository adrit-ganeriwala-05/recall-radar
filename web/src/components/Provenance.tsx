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

/** PROJECT_SPEC §5: when availability falls back to LDATE+7, every screen says "received-date experiment". */
export function ReceivedDateNote({ provenance }: { provenance: Provenance }) {
  if (provenance.availability_basis !== "LDATE_PLUS_7") return null;
  return (
    <span className="badge badge-offline" data-testid="received-date-note">
      Received-date experiment: a complaint counts as public 7 days after NHTSA received it
    </span>
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
        <ReceivedDateNote provenance={provenance} />
      </p>
    </>
  );
}
