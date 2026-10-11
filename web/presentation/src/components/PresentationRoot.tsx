// Owner: C. Isolated root of the presentation and owner of its stacking order:
//   z-0  SceneLayer      fixed, full-viewport, pointer-events:none (added in Phase 2)
//   z-10 InterfaceLayer  normal document flow; sets the page height
//   z-30 header          sticky navigation
//   z-50 dialogs         (Phase 3)
// `isolate` creates the stacking context here so no ancestor transform or negative z-index can
// push a fixed canvas above or below the page. No transforms are applied to this element, so a
// position:fixed child stays relative to the viewport.
import type { ReactNode } from "react";

type Props = {
  header: ReactNode;
  children: ReactNode;
};

export function PresentationRoot({ header, children }: Props) {
  return (
    <div className="relative isolate min-h-dvh bg-graphite text-ink">
      {header}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
