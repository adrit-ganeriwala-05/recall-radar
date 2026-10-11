// Owner: C. PRD v2 F3.4: the F1 card for a recall marker, in a dialog; Esc/close returns focus to the marker.
// Motion: the drawer slides in from the right and the modal backdrop fades (ui/motion.ts); the parent
// wraps it in AnimatePresence so both also animate out. Clicking the backdrop closes it like Esc.
import { motion } from "motion/react";
import { useEffect, useRef } from "react";
import { backdropMotion, useMotionPresets } from "../ui/motion";
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
  const mp = useMotionPresets();
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <>
      <motion.div className="drawer-backdrop" aria-hidden="true" onClick={onClose} {...backdropMotion} />
      <motion.div className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-h" data-testid="recall-drawer" {...mp.drawer}>
      <div className="drawer-head">
        <h2 id="drawer-h">Recall campaign {campno}</h2>
        <motion.button type="button" ref={closeRef} onClick={onClose} {...mp.buttonTap}>
          Close
        </motion.button>
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
      </motion.div>
    </>
  );
}
