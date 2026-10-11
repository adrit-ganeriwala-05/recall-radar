import { cleanup } from "@testing-library/react";
import { afterEach, beforeAll } from "vitest";
import { preloadCharts } from "../charts";

afterEach(() => cleanup());
// Chart modules are code-split (lazy); load them once so charts render on the first pass, as they do
// in the browser once the module has arrived.
beforeAll(() => preloadCharts());

// jsdom has no layout engine. These stand-ins let the real Bklit charts render in tests:
//  - ResizeObserver reports a fixed 800 x 400 box (visx ParentSize needs a measured size);
//  - IntersectionObserver reports every element as visible (charts mount on first visibility,
//    sections animate in view);
//  - matchMedia answers from `testMedia` (tests can switch reduced motion or the phone layout on).
export const testMedia = { reducedMotion: false, compact: false };

class TestResizeObserver {
  constructor(private readonly cb: ResizeObserverCallback) {}
  observe(target: Element) {
    const rect = { width: 800, height: 400, top: 0, left: 0, right: 800, bottom: 400, x: 0, y: 0, toJSON: () => ({}) };
    this.cb([{ target, contentRect: rect } as unknown as ResizeObserverEntry], this as unknown as ResizeObserver);
  }
  unobserve() {}
  disconnect() {}
}

class TestIntersectionObserver {
  constructor(private readonly cb: IntersectionObserverCallback) {}
  observe(target: Element) {
    this.cb([{ target, isIntersecting: true, intersectionRatio: 1 } as unknown as IntersectionObserverEntry], this as unknown as IntersectionObserver);
  }
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
}

const g = globalThis as unknown as Record<string, unknown>;
g.ResizeObserver ??= TestResizeObserver;
g.IntersectionObserver ??= TestIntersectionObserver;
if (typeof window !== "undefined") {
  window.matchMedia = ((query: string) => {
    const matches = /prefers-reduced-motion:\s*reduce/.test(query) ? testMedia.reducedMotion : /max-width:\s*639px/.test(query) ? testMedia.compact : false;
    return {
      matches,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    } as unknown as MediaQueryList;
  }) as typeof window.matchMedia;
}
