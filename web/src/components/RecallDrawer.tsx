// Owner: C. PRD v2 F3.4: the F1 card for a recall marker, in a dialog; Esc/close returns focus to the marker.
import { useEffect, useRef } from "react";
import type { RecallCampaign, VehicleKey } from "../contracts.gen";
import { RecallCard } from "./RecallCard";

export function RecallDrawer({
  campno,
  link,
  campaign,
  loading,
  vehicle,
  dataAsOf,
  onClose,
}: {
  campno: string;
  link?: "issue" | "vehicle" | null;
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
      ) : link === "issue" ? (
        // B's finding on #36: an investigation's campaign often names other model years or models. Showing that
        // row's card would claim it covers this vehicle (F1.2), so say what is true instead.
        <p className="state" data-testid="recall-other-vehicles">
          Campaign {campno} is linked to the NHTSA investigation of this issue. NHTSA&apos;s recall file does not list the{" "}
          {vehicle.model_year} {vehicle.make} {vehicle.model} under this campaign; it lists other model years or models.{" "}
          <a href="https://www.nhtsa.gov/recalls" target="_blank" rel="noopener noreferrer">
            Check a specific car by VIN →
          </a>
        </p>
      ) : (
        <p className="state" data-testid="recall-unavailable">
          Record unavailable: campaign {campno} is not in this cached dataset for the {vehicle.model_year} {vehicle.make}{" "}
          {vehicle.model}.
        </p>
      )}
    </div>
  );
}
