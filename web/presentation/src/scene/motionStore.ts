"use client";
// Owner: C. The page's single MotionState and the way writers outside the R3F canvas ask for a frame.
// One instance per page load (module scope holds only a plain object — no browser API is touched at
// import time, so this is safe in the server build). SceneLayer registers R3F's invalidate() here;
// the ScrollDirector and pointer tracker write targets and call requestFrame().
import { createMotionState } from "./motionState";

export const motion = createMotionState();

let frameRequester: (() => void) | null = null;

export function setFrameRequester(fn: (() => void) | null) {
  frameRequester = fn;
}

export function requestFrame() {
  frameRequester?.();
}

/**
 * What the scene layer ended up running, published so the ScrollDirector can decide whether scroll
 * choreography is affordable: "pending" until the canvas exists, then "hardware" or "software" WebGL,
 * or "fallback" (static illustration). Choreography runs only on "hardware": under software WebGL every
 * scroll-driven camera move renders frames that starve the browser's compositor, which was measured to
 * stall native keyboard scrolling (see ARCHITECTURE.md §11). Mirrored on <html data-scene-renderer>.
 */
export type SceneKind = "pending" | "hardware" | "software" | "fallback";

let sceneKind: SceneKind = "pending";
const sceneKindListeners = new Set<() => void>();

export function getSceneKind(): SceneKind {
  return sceneKind;
}

export function setSceneKind(kind: SceneKind) {
  if (kind === sceneKind) return;
  sceneKind = kind;
  document.documentElement.dataset.sceneRenderer = kind;
  for (const listener of sceneKindListeners) listener();
}

export function onSceneKindChange(listener: () => void): () => void {
  sceneKindListeners.add(listener);
  return () => sceneKindListeners.delete(listener);
}
