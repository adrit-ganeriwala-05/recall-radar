// Owner: C. Conservative quality tiers, decided once on mount (browser only; never at module scope).
// Targets a normal judge laptop: device-pixel-ratio is capped, and the low tier drops the glass
// transmission pass (an extra full render of the scene) and halves the contact-shadow resolution.

export type QualityTier = "high" | "low";

export type QualitySettings = {
  tier: QualityTier;
  dpr: [number, number];
  shadowResolution: number;
  /** Keep KHR_materials_transmission glass (costs one extra scene render per frame). */
  transmission: boolean;
  /** MSAA on the default framebuffer. */
  antialias: boolean;
};

const SETTINGS: Record<QualityTier, QualitySettings> = {
  high: { tier: "high", dpr: [1, 1.75], shadowResolution: 1024, transmission: true, antialias: true },
  low: { tier: "low", dpr: [1, 1.25], shadowResolution: 512, transmission: false, antialias: false },
};

export function detectQuality(): QualitySettings {
  const cores = navigator.hardwareConcurrency ?? 4;
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? 8;
  const coarsePointer = window.matchMedia("(pointer: coarse)").matches;
  const low = cores <= 4 || memory <= 4 || coarsePointer;
  return SETTINGS[low ? "low" : "high"];
}
