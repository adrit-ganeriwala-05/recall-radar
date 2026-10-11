// Owner: C. The canvas-to-HTML contract (ARCHITECTURE.md §5).
// One small mutable object per page, never React state: writers set targets, and SceneController is
// the only code that turns them into camera/model transforms. Writers: the pointer tracker, the
// development composition inspector, SceneController itself (hero stage), and the ScrollDirector
// (scroll path + chapter stages, Phase 4).

export type ChapterId = "intro" | "overview" | "explore" | "record" | "official" | "report" | "closing";

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
  /** Size relative to the chapter stage (1 = as large as the stage allows); lower = less prominent. */
  size: number;
  /** Opacity of the whole scene layer in this chapter (the ScrollDirector applies it). */
  opacity: number;
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
  /**
   * Scroll-driven blend between two chapters (ScrollDirector, Phase 4): t = 0 → `from`, 1 → `to`.
   * null when choreography is off (narrow layouts, reduced motion): the chapter field applies.
   */
  path: { from: ChapterId; to: ChapterId; t: number } | null;
  /** Per-chapter framing measured from each section's right-hand stage column (ScrollDirector). */
  chapterStages: Partial<Record<ChapterId, { anchor: { x: number; y: number }; fill: number }>>;
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
  // Hero and "How it works": front three-quarter, nose toward screen-left.
  intro: {
    wide: { direction: [4.6, 1.55, 5.9], target: [0, 0.48, 0], fov: 30, anchor: { x: 0.71, y: 0.56 }, fill: 0.6, yaw: 0, size: 1, opacity: 1 },
    narrow: { direction: [4.6, 1.7, 5.9], target: [0, 0.48, 0], fov: 30, anchor: { x: 0.5, y: 0.25 }, fill: 0.95, yaw: 0, size: 1, opacity: 1 },
  },
  // How it works: the same front three-quarter, framed in this section's own stage column (its text
  // column is wider than the hero's copy, so keeping the hero framing would put the car behind text).
  overview: {
    wide: { direction: [4.6, 1.55, 5.9], target: [0, 0.48, 0], fov: 30, anchor: { x: 0.74, y: 0.5 }, fill: 0.5, yaw: 0, size: 0.95, opacity: 1 },
    narrow: { direction: [4.6, 1.7, 5.9], target: [0, 0.48, 0], fov: 30, anchor: { x: 0.5, y: 0.25 }, fill: 0.95, yaw: 0, size: 1, opacity: 1 },
  },
  // Explore: turned toward a side view, beside the evidence panel.
  explore: {
    wide: { direction: [8.2, 1.25, 0.6], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.72, y: 0.52 }, fill: 0.5, yaw: 0, size: 0.95, opacity: 1 },
    narrow: { direction: [8.2, 1.4, 0.6], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.5, y: 0.3 }, fill: 0.95, yaw: 0, size: 1, opacity: 1 },
  },
  // Follow the record: higher, smaller — the timeline text is the focus.
  record: {
    wide: { direction: [7.2, 2.9, 7.4], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.8, y: 0.36 }, fill: 0.42, yaw: 0.35, size: 0.7, opacity: 0.85 },
    narrow: { direction: [7.2, 3.2, 7.4], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.5, y: 0.22 }, fill: 0.8, yaw: 0.35, size: 1, opacity: 1 },
  },
  // Official information: calm rear three-quarter from the same side (a small swing, nothing dramatic).
  official: {
    wide: { direction: [6.5, 2.0, -3.5], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.78, y: 0.5 }, fill: 0.5, yaw: 0, size: 0.8, opacity: 0.85 },
    narrow: { direction: [6.5, 2.2, -3.5], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.5, y: 0.26 }, fill: 0.9, yaw: 0, size: 1, opacity: 1 },
  },
  // Evidence: farther and softer so the document cards lead.
  report: {
    wide: { direction: [8.6, 3.4, 8.8], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.86, y: 0.4 }, fill: 0.34, yaw: 0.5, size: 0.55, opacity: 0.4 },
    narrow: { direction: [8.6, 3.8, 8.8], target: [0, 0.4, 0], fov: 30, anchor: { x: 0.5, y: 0.2 }, fill: 0.7, yaw: 0.5, size: 1, opacity: 1 },
  },
  // Continue: a composed final front three-quarter; it settles and stops.
  closing: {
    wide: { direction: [4.9, 1.35, 5.3], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.69, y: 0.55 }, fill: 0.62, yaw: -0.15, size: 0.95, opacity: 1 },
    narrow: { direction: [4.9, 1.6, 5.3], target: [0, 0.5, 0], fov: 30, anchor: { x: 0.5, y: 0.3 }, fill: 0.95, yaw: -0.15, size: 1, opacity: 1 },
  },
};

export const CHAPTERS = Object.keys(COMPOSITIONS) as ChapterId[];

/** Wide layout = the hero's two-column grid (Tailwind `lg`, 1024 px). */
export const WIDE_MIN_WIDTH = 1024;

export function compositionFor(chapter: ChapterId, viewportWidth: number): Composition {
  const c = COMPOSITIONS[chapter];
  return viewportWidth >= WIDE_MIN_WIDTH ? c.wide : c.narrow;
}

/** One chapter's composition with its measured stage applied (hero stage for intro, else chapter stage). */
export function resolvedComposition(motion: MotionState, chapter: ChapterId, viewportWidth: number): Composition {
  const base = compositionFor(chapter, viewportWidth);
  const stage = chapter === "intro" ? motion.stage : motion.chapterStages[chapter];
  if (!stage) return base;
  return { ...base, anchor: stage.anchor, fill: stage.fill * base.size };
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const lerp3 = (a: Vec3, b: Vec3, t: number): Vec3 => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
/** Gentle in/out over each scrubbed transition, so the car never starts or stops abruptly. */
export const smoothstep = (t: number) => {
  const x = Math.min(1, Math.max(0, t));
  return x * x * (3 - 2 * x);
};

export function blendCompositions(a: Composition, b: Composition, t: number): Composition {
  const s = smoothstep(t);
  return {
    direction: lerp3(a.direction, b.direction, s),
    target: lerp3(a.target, b.target, s),
    fov: lerp(a.fov, b.fov, s),
    anchor: { x: lerp(a.anchor.x, b.anchor.x, s), y: lerp(a.anchor.y, b.anchor.y, s) },
    fill: lerp(a.fill, b.fill, s),
    yaw: lerp(a.yaw, b.yaw, s),
    size: lerp(a.size, b.size, s),
    opacity: lerp(a.opacity, b.opacity, s),
  };
}

/** The composition actually used: the scroll path when choreography runs, otherwise the chapter. */
export function activeComposition(motion: MotionState, viewportWidth: number): Composition {
  if (motion.path) {
    const a = resolvedComposition(motion, motion.path.from, viewportWidth);
    if (motion.path.from === motion.path.to) return a;
    return blendCompositions(a, resolvedComposition(motion, motion.path.to, viewportWidth), motion.path.t);
  }
  return resolvedComposition(motion, motion.chapter, viewportWidth);
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
  return { chapter: "intro", progress: 0, stage: null, stageDirty: true, path: null, chapterStages: {}, pointer: { x: 0, y: 0 }, reducedMotion: false };
}
