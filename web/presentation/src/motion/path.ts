// Owner: C. Pure scroll-to-chapter mapping for the Phase 4 choreography: no DOM, no GSAP, so it can be
// reasoned about and tested on its own (e2e/choreography.spec.ts). ScrollDirector measures the page
// on ScrollTrigger refresh and calls these; nothing here runs per frame except pathAt.
import type { ChapterId } from "@/scene/motionState";

export type Transition = { from: ChapterId; to: ChapterId; start: number; end: number };
export type Path = { from: ChapterId; to: ChapterId; t: number };

/** A transition runs while the incoming section's top travels from 85% to 35% of the viewport height. */
export const WINDOW_START = 0.85;
export const WINDOW_END = 0.35;

/**
 * Transitions from the page-order chapter sections (`top` in document px; `first` is the chapter shown
 * before any section arrives). Two guards keep the camera path continuous and complete:
 *  - a transition never starts before the previous one ends (very short sections or viewports would
 *    otherwise make the path jump backwards mid-blend);
 *  - every transition finishes by `maxScroll`, so the last chapter is reached at the bottom of the
 *    page however short the final section is.
 * Blends keep a non-zero length wherever there is scroll room (up to 1 px each when squeezed), so the
 * path stays ordered; only in extreme layouts does a blend become that short.
 */
export function buildTransitions(
  sections: { chapter: ChapterId; top: number }[],
  first: ChapterId,
  viewportHeight: number,
  maxScroll: number,
): Transition[] {
  const out: Transition[] = [];
  let from = first;
  let prevEnd = 0;
  for (const { chapter, top } of sections) {
    const start = Math.max(top - WINDOW_START * viewportHeight, prevEnd);
    const end = Math.max(top - WINDOW_END * viewportHeight, start + 1);
    out.push({ from, to: chapter, start, end });
    from = chapter;
    prevEnd = end;
  }
  let limit = Math.max(0, maxScroll);
  for (let i = out.length - 1; i >= 0; i--) {
    const tr = out[i];
    tr.end = Math.min(tr.end, limit);
    // Leave room before this blend for the i earlier ones: 1 px, or an equal share when squeezed.
    tr.start = Math.min(tr.start, tr.end - Math.min(1, tr.end / (i + 1)));
    limit = tr.start;
  }
  return out;
}

/** Which chapters a scroll position sits between, and how far through the blend (0..1). */
export function pathAt(scroll: number, transitions: Transition[], first: ChapterId = "intro"): Path {
  let path: Path = { from: first, to: first, t: 0 };
  for (const tr of transitions) {
    if (scroll < tr.start) break;
    path = scroll >= tr.end ? { from: tr.to, to: tr.to, t: 0 } : { from: tr.from, to: tr.to, t: (scroll - tr.start) / (tr.end - tr.start) };
  }
  return path;
}
