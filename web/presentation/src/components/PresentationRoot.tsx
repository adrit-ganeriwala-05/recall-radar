// Owner: C. Isolated root of the presentation and owner of its stacking order:
//   z-0  SceneLayer      fixed, full-viewport, pointer-events:none (SceneLayerLoader)
//   z-10 InterfaceLayer  normal document flow; sets the page height
//   z-30 header          sticky navigation
//   z-50 dialogs         (Phase 3)
// `isolate` creates the stacking context here so no ancestor transform or negative z-index can
// push a fixed canvas above or below the page. No transforms are applied to this element, so a
// position:fixed child stays relative to the viewport.
import type { ReactNode } from "react";

type Props = {
  /** Layer 1 (fixed, z-0). Rendered first so it paints beneath everything else. */
  scene: ReactNode;
  header: ReactNode;
  children: ReactNode;
};

export function PresentationRoot({ scene, header, children }: Props) {
  return (
    <div className="relative isolate min-h-dvh bg-graphite text-ink">
      {scene}
      {header}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
