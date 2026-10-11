// Owner: C. The canvas-to-HTML contract (ARCHITECTURE.md §5).
// One small mutable object per page, never React state: writers set targets, and SceneController is
// the only code that turns them into camera/model transforms. Phase 2 writers: the pointer tracker
// and the development composition inspector. Phase 4 adds the scroll director as the chapter writer.

export type ChapterId = "intro" | "explore" | "record" | "official" | "report" | "closing";

export type Vec3 = readonly [number, number, number];

/** A camera framing in the model's normalized space (car length 4, ground at y = 0, nose toward +z). */
export type Composition = {
  /** Direction from the target to the camera (any length; only the direction is used). */
  direction: Vec3;
  target: Vec3;
  fov: number;
  /** Where the car's centre lands on screen, as fractions of the viewport (0,0 = top-left). */
  anchor: { x: number; y: number };
  /**
   * Share of the viewport width the model's bounding sphere may span. The camera distance is solved
   * from this, the measured sphere radius and the current aspect ratio, so framing holds at any size.
   */
  fill: number;
  /** Base yaw of the car in radians (0 = as authored). */
  yaw: number;
};

export type ResponsiveComposition = { wide: Composition; narrow: Composition };

export type MotionState = {
  chapter: ChapterId;
  /** 0..1 progress inside the chapter (written by the Phase 4 scroll director; unused in Phase 2). */
  progress: number;
  /**
   * Hero framing measured from the DOM stage (see stage.ts); null until measured. Overrides the
   * authored anchor/fill of the "intro" chapter so the car follows the real layout.
   */
  stage: { anchor: { x: number; y: number }; fill: number } | null;
  /** Set when the DOM stage may have changed (fonts, layout); SceneController re-measures and clears it. */
  stageDirty: boolean;
  /** -1..1 mouse position over the viewport; touch never writes it. */
  pointer: { x: number; y: number };
  reducedMotion: boolean;
};

/**
 * Planned compositions, authored against the measured asset (length 4.36 m before normalization,
 * nose at +z): a camera in the +x/+z quadrant shows the front three-quarter with the nose toward
 * screen-left. Wide layouts put the car in the right ~58% column; narrow layouts put it above the copy.
 */
export const COMPOSITIONS: Record<ChapterId, ResponsiveComposition> = {
  intro: {
    wide: { direction: [4.6, 1.55, 5.9], target: [0, 0.48, 0], fov: 30, anchor: { x: 0.71, y: 0.56 }, fill: 0.6, yaw: 0 },
    narrow: { direction: [4.6, 1.7, 5.9], target: [0, 0.48, 0], fov: 30, anchor: { x: 0.5, y: 0.25 }, fill: 0.95, yaw: 0 },
  },
  explore: {
    wide: { direction: [8.2, 1.25, 0.6], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.72, y: 0.52 }, fill: 0.5, yaw: 0 },
    narrow: { direction: [8.2, 1.4, 0.6], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.5, y: 0.3 }, fill: 0.95, yaw: 0 },
  },
  record: {
    wide: { direction: [7.2, 2.9, 7.4], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.8, y: 0.36 }, fill: 0.42, yaw: 0.35 },
    narrow: { direction: [7.2, 3.2, 7.4], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.5, y: 0.22 }, fill: 0.8, yaw: 0.35 },
  },
  official: {
    wide: { direction: [-5.8, 1.7, 4.9], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.78, y: 0.5 }, fill: 0.5, yaw: 0 },
    narrow: { direction: [-5.8, 1.9, 4.9], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.5, y: 0.26 }, fill: 0.9, yaw: 0 },
  },
  report: {
    wide: { direction: [8.6, 3.4, 8.8], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.86, y: 0.4 }, fill: 0.34, yaw: 0.5 },
    narrow: { direction: [8.6, 3.8, 8.8], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.5, y: 0.2 }, fill: 0.7, yaw: 0.5 },
  },
  closing: {
    wide: { direction: [4.9, 1.35, 5.3], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.69, y: 0.55 }, fill: 0.62, yaw: -0.15 },
    narrow: { direction: [4.9, 1.6, 5.3], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.5, y: 0.3 }, fill: 0.95, yaw: -0.15 },
  },
};

export const CHAPTERS = Object.keys(COMPOSITIONS) as ChapterId[];

/** Wide layout = the hero's two-column grid (Tailwind `lg`, 1024 px). */
export const WIDE_MIN_WIDTH = 1024;

export function compositionFor(chapter: ChapterId, viewportWidth: number): Composition {
  const c = COMPOSITIONS[chapter];
  return viewportWidth >= WIDE_MIN_WIDTH ? c.wide : c.narrow;
}

/** The composition actually used: the hero takes its anchor and fill from the measured stage. */
export function activeComposition(motion: MotionState, viewportWidth: number): Composition {
  const base = compositionFor(motion.chapter, viewportWidth);
  if (motion.chapter === "intro" && motion.stage) return { ...base, anchor: motion.stage.anchor, fill: motion.stage.fill };
  return base;
}

/** Normalized-space bounding-sphere radius used until the model reports its measured one. */
export const DEFAULT_MODEL_RADIUS = 2.4;

/**
 * Camera distance at which a sphere of `radius` spans `fill` of the viewport width, for a vertical fov
 * (degrees) and a width/height aspect. Width only: a bounding sphere greatly overstates a car's height,
 * so a height term would shrink wide layouts. Clamped to a sane range for extreme aspect ratios.
 */
export function fitDistance(radius: number, fill: number, fovDeg: number, aspect: number): number {
  const tanV = Math.tan((fovDeg * Math.PI) / 360);
  return Math.min(40, Math.max(4, radius / (fill * tanV * aspect)));
}

export function createMotionState(): MotionState {
  return { chapter: "intro", progress: 0, stage: null, stageDirty: true, pointer: { x: 0, y: 0 }, reducedMotion: false };
}
