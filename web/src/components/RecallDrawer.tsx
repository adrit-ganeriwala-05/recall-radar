// Owner: C. PRD v2 F3.4: the F1 card for a recall marker, in a dialog; Esc/close returns focus to the marker.
import { useEffect, useRef } from "react";
import type { RecallCampaign, VehicleKey } from "../contracts.gen";
import { RecallCard } from "./RecallCard";

export function RecallDrawer({
  campno,
  campaign,
  loading,
  vehicle,
  dataAsOf,
  onClose,
}: {
  campno: string;
  campaign: RecallCampaign | undefined;
  loading: boolean;
  vehicle: VehicleKey;
  dataAsOf?: string | null;
  onClose: () => void;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-h" data-testid="recall-drawer">
      <div className="drawer-head">
        <h2 id="drawer-h">Recall campaign {campno}</h2>
        <button type="button" ref={closeRef} onClick={onClose}>
          Close
        </button>
      </div>
      {loading ? (
        <p className="state">Loading the campaign…</p>
      ) : campaign ? (
        <RecallCard campaign={campaign} vehicle={vehicle} dataAsOf={dataAsOf} />
      ) : (
        <p className="state" data-testid="recall-unavailable">
          Record unavailable: campaign {campno} is not in this cached dataset for the {vehicle.model_year} {vehicle.make}{" "}
          {vehicle.model}.
        </p>
      )}
    </div>
  );
}
