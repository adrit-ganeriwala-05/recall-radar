// Owner: C. The fixed background layer (z-0) that hosts either the WebGL canvas or the static
// fallback. pointer-events:none, so every HTML control above it receives input normally; it never
// owns scrolling. The soft studio floor glow is CSS (so it shows before and without WebGL); it sits
// under the car at each layout's composition anchor, which is what lets the contact shadow read.
import type { ReactNode } from "react";

export function SceneFrame({ state, children }: { state: string; children: ReactNode }) {
  return (
    <div
      aria-hidden="true"
      data-scene-state={state}
      className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(48%_16%_at_50%_31%,rgb(245_242_235/0.09),transparent_75%)] lg:bg-[radial-gradient(30%_17%_at_71%_70%,rgb(245_242_235/0.1),transparent_75%)]"
    >
      {children}
    </div>
  );
}
