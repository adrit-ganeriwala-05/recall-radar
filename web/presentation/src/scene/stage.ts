"use client";
// Owner: C. The hero reserves a "stage" box for the car ([data-scene-stage]: the right column in the
// wide layout, the space above the copy in the narrow one). The fixed scene layer frames the car,
// its floor glow and the static fallback from this measured box instead of fixed viewport fractions,
// so framing follows the real layout at every size (ultrawide containers, short landscape, zoom,
// foldable segments). Measured in document coordinates, i.e. as laid out at the top of the page.
import { useEffect, useState } from "react";

export type Stage = { left: number; top: number; width: number; height: number; viewportWidth: number; viewportHeight: number };

export function measureStage(): Stage | null {
  for (const el of document.querySelectorAll<HTMLElement>("[data-scene-stage]")) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) {
      return {
        left: r.left + window.scrollX,
        top: r.top + window.scrollY,
        width: r.width,
        height: r.height,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
      };
    }
  }
  return null;
}

function same(a: Stage | null, b: Stage | null): boolean {
  if (!a || !b) return a === b;
  return (
    Math.abs(a.left - b.left) < 0.5 &&
    Math.abs(a.top - b.top) < 0.5 &&
    Math.abs(a.width - b.width) < 0.5 &&
    Math.abs(a.height - b.height) < 0.5 &&
    a.viewportWidth === b.viewportWidth &&
    a.viewportHeight === b.viewportHeight
  );
}

/** Re-measures on resize, orientation change, font/layout changes; at most once per animation frame. */
export function useSceneStage(): Stage | null {
  const [stage, setStage] = useState<Stage | null>(null);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => setStage((prev) => {
        const next = measureStage();
        return same(prev, next) ? prev : next;
      }));
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(document.documentElement);
    document.querySelectorAll("[data-scene-stage]").forEach((el) => observer.observe(el));
    window.addEventListener("resize", update);
    window.addEventListener("orientationchange", update);
    void document.fonts?.ready.then(update);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("resize", update);
      window.removeEventListener("orientationchange", update);
    };
  }, []);

  return stage;
}

/**
 * Screen anchor (fractions of the viewport) and sphere fill for the hero framing: the car centred in
 * the stage, its bounding sphere as wide as the stage allows. The projected car is ~0.45 as tall as
 * it is wide in the three-quarter view, so very flat stages cap the width by height.
 */
export function stageFraming(stage: Stage): { anchor: { x: number; y: number }; fill: number } {
  const sphereWidthPx = Math.min(stage.width, stage.height * 2.2);
  return {
    anchor: {
      x: (stage.left + stage.width / 2) / stage.viewportWidth,
      y: (stage.top + stage.height / 2) / stage.viewportHeight,
    },
    fill: sphereWidthPx / stage.viewportWidth,
  };
}
