// Owner: C. The fixed background layer (z-0) that hosts either the WebGL canvas or the static
// fallback. pointer-events:none, so every HTML control above it receives input normally; it never
// owns scrolling. The soft studio floor glow is CSS (shown before and without WebGL) and is placed
// under the car from the measured hero stage, which is what lets the contact shadow read.
import type { ReactNode } from "react";
import type { Stage } from "@/scene/stage";

type Props = { state: string; stage: Stage | null; children: ReactNode };

export function SceneFrame({ state, stage, children }: Props) {
  return (
    <div aria-hidden="true" data-scene-state={state} className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {stage && (
        <div
          className="absolute rounded-[50%] bg-[radial-gradient(closest-side,rgb(245_242_235/0.1),transparent)]"
          style={{
            left: stage.left + stage.width * 0.05,
            top: stage.top + stage.height * 0.55,
            width: stage.width * 0.9,
            height: stage.height * 0.5,
          }}
        />
      )}
      {children}
    </div>
  );
}
