// Owner: C. The fixed background layer (z-0) that hosts either the WebGL canvas or the static
// fallback. pointer-events:none, so every HTML control above it receives input normally; it never
// owns scrolling. The studio light is CSS (shown before and without WebGL): a soft overhead softbox, a
// cool key light and a floor glow placed from the measured hero stage (which lets the contact shadow
// read), and a gentle vignette over everything. Opacities come from CSS variables owned by the
// ScrollDirector (default 1), so elements mounted later pick them up.
import type { ReactNode } from "react";
import type { Stage } from "@/scene/stage";

type Props = { state: string; stage: Stage | null; children: ReactNode };

export function SceneFrame({ state, stage, children }: Props) {
  return (
    <div aria-hidden="true" data-scene-state={state} className="pointer-events-none fixed inset-0 z-0 overflow-hidden [opacity:var(--rr-scene-opacity,1)]">
      <div className="absolute left-1/2 top-[-28vh] h-[62vh] w-[90vw] -translate-x-1/2 rounded-[50%] bg-[radial-gradient(closest-side,rgb(244_240_232/0.07),transparent)]" />
      {stage && (
        <>
          <div
            data-scene-light
            className="absolute rounded-[50%] [opacity:var(--rr-glow-opacity,1)] bg-[radial-gradient(closest-side,rgb(134_165_255/0.10),rgb(134_165_255/0.03)_55%,transparent)]"
            style={{
              left: stage.left - stage.width * 0.2,
              top: stage.top - stage.height * 0.35,
              width: stage.width * 1.4,
              height: stage.height * 1.5,
            }}
          />
          <div
            data-scene-glow
            className="absolute rounded-[50%] [opacity:var(--rr-glow-opacity,1)] bg-[radial-gradient(closest-side,rgb(245_242_235/0.11),transparent)]"
            style={{
              left: stage.left + stage.width * 0.05,
              top: stage.top + stage.height * 0.55,
              width: stage.width * 0.9,
              height: stage.height * 0.5,
            }}
          />
        </>
      )}
      {children}
      <div className="absolute inset-0 bg-[radial-gradient(130%_95%_at_55%_40%,transparent_55%,rgb(0_0_0/0.55))]" />
    </div>
  );
}
