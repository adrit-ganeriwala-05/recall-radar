"use client";
// Owner: C. Phase 4 scroll choreography — the single owner of: the Lenis instance and its GSAP-ticker
// drive, the page's ScrollTriggers, motion.path / motion.chapterStages (read by SceneController, the
// only camera writer), and the --rr-scene-opacity / --rr-glow-opacity variables on <html>.
// Modes (gsap.matchMedia): choreography only in the wide layout with motion allowed (CHOREO_QUERY) and
// only while the scene runs on hardware WebGL (motionStore scene kind; software rendering and the
// static fallback keep it off); a short HTML entrance wherever motion is allowed; nothing under
// prefers-reduced-motion. While choreography runs, <html data-choreo="on"> drives the `choreo` CSS
// variant, so CSS can never disagree with JS. Layout is measured on ScrollTrigger refresh, never per frame.
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { useEffect } from "react";
import { COMPOSITIONS, smoothstep, type ChapterId } from "@/scene/motionState";
import { getSceneKind, motion, onSceneKindChange, requestFrame } from "@/scene/motionStore";
import { buildTransitions, pathAt, type Transition } from "./path";

/** Where choreography may run (wide layout, motion allowed); the scene kind must also be "hardware". */
export const CHOREO_QUERY =
  "(prefers-reduced-motion: no-preference) and (min-width: 1024px), (prefers-reduced-motion: no-preference) and (min-aspect-ratio: 27/20) and (min-width: 560px), (prefers-reduced-motion: no-preference) and (horizontal-viewport-segments: 2)";
const MOTION_OK = "(prefers-reduced-motion: no-preference)";

/** Chapters in page order; the hero is "intro", each later chapter is a section carrying data-chapter. */
const ORDER: ChapterId[] = ["intro", "overview", "explore", "record", "official", "report", "closing"];

export function ScrollDirector() {
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const mm = gsap.matchMedia();
    const root = document.documentElement;

    // HTML entrance, any width: a 14 px upward settle, no fading, so text is never hidden.
    mm.add(MOTION_OK, () => {
      for (const el of gsap.utils.toArray<HTMLElement>("[data-reveal]")) {
        gsap.from(el, { y: 14, duration: 0.4, ease: "power2.out", scrollTrigger: { trigger: el, start: "top 90%", once: true } });
      }
    });

    const choreography = () => {
      root.dataset.choreo = "on";
      const lenis = new Lenis({ autoRaf: false, prevent: (node) => Boolean(node.closest("[data-lenis-prevent]")) });
      lenis.on("scroll", ScrollTrigger.update);
      // GSAP's ticker drives Lenis (seconds → ms); Lenis runs no animation frame loop of its own.
      const tick = (time: number) => lenis.raf(time * 1000);
      gsap.ticker.add(tick);
      gsap.ticker.lagSmoothing(0);

      // In-page links scroll smoothly through Lenis and keep the URL hash (back/forward work). Lenis
      // subtracts the page's scroll-padding-top (5rem, so it follows text size), the same offset native
      // jumps use, so targets land below the sticky header. Focus moves to the target's heading, as a
      // native fragment jump moves the keyboard starting point: keyboard and screen-reader users continue
      // from where they went (mouse users see no ring, since focus left a pointer-clicked link). A wheel
      // during the scroll takes over from the current position (Lenis keeps its target there while a
      // programmatic scroll runs); keys and pointer presses cancel it, so native keyboard scrolling and
      // scrollbar drags are never overridden. The skip link stays native.
      let anchoring = false;
      const cancelAnchor = () => {
        if (!anchoring) return;
        anchoring = false;
        lenis.stop(); // stop + start = drop the animation and resync to the real scroll position
        lenis.start();
      };
      const onClick = (event: MouseEvent) => {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const link = (event.target as Element | null)?.closest<HTMLAnchorElement>('a[href^="#"]');
        const hash = link?.getAttribute("href");
        if (!link || !hash || hash === "#" || hash === "#main") return;
        const target = document.querySelector<HTMLElement>(hash);
        if (!target) return;
        event.preventDefault();
        if (location.hash !== hash) history.pushState(null, "", hash);
        anchoring = true;
        lenis.scrollTo(target, { onComplete: () => (anchoring = false) });
        const heading = target.matches("h1, h2") ? target : target.querySelector<HTMLElement>("h1, h2");
        const focusTarget = heading ?? target;
        if (!focusTarget.hasAttribute("tabindex")) focusTarget.setAttribute("tabindex", "-1");
        focusTarget.focus({ preventScroll: true });
      };
      document.addEventListener("click", onClick);
      window.addEventListener("keydown", cancelAnchor, true);
      window.addEventListener("pointerdown", cancelAnchor, true);

      let transitions: Transition[] = [];
      const measure = () => {
        const vh = window.innerHeight;
        const vw = window.innerWidth;
        const sy = window.scrollY;
        const sections: { chapter: ChapterId; top: number }[] = [];
        for (const chapter of ORDER.slice(1)) {
          const section = document.querySelector<HTMLElement>(`section[data-chapter="${chapter}"]`);
          if (section) sections.push({ chapter, top: section.getBoundingClientRect().top + sy });
        }
        transitions = buildTransitions(sections, ORDER[0], vh, ScrollTrigger.maxScroll(window));
        root.dataset.chapterMeasured = String(document.documentElement.scrollHeight); // diagnostics: layout measured
        motion.chapterStages = {};
        for (const ch of ORDER.slice(1)) {
          const r = document.querySelector<HTMLElement>(`[data-chapter-stage="${ch}"]`)?.getBoundingClientRect();
          if (!r || r.width === 0) continue;
          // Centred in the section's stage column, at mid-viewport height; as wide as the column allows
          // but never taller than the viewport can show comfortably.
          motion.chapterStages[ch] = { anchor: { x: (r.left + r.width / 2) / vw, y: 0.5 }, fill: Math.min(r.width, vh) / vw };
        }
      };
      const apply = (scroll: number) => {
        const path = pathAt(scroll, transitions);
        motion.path = path;
        const s = smoothstep(path.t);
        const from = COMPOSITIONS[path.from].wide.opacity;
        const to = COMPOSITIONS[path.to].wide.opacity;
        root.style.setProperty("--rr-scene-opacity", String(from + (to - from) * s));
        root.style.setProperty("--rr-glow-opacity", String(path.from === "intro" ? (path.to === "intro" ? 1 : 1 - s) : 0));
        root.dataset.chapterPath = `${path.from}>${path.to}:${path.t.toFixed(2)}`;
        // Diagnostics read by the e2e suite: the scroll position this path was computed for, and how many
        // ScrollTriggers exist (cleanup must not leak them).
        root.dataset.chapterScroll = String(Math.round(scroll));
        root.dataset.scrollTriggers = String(ScrollTrigger.getAll().length);
        requestFrame();
      };
      const trigger = ScrollTrigger.create({
        start: 0,
        end: "max",
        onRefresh: (self) => {
          measure();
          apply(self.scroll());
        },
        onUpdate: (self) => apply(self.scroll()),
      });

      // Layout changes after load (data sections filling in, fonts) → one debounced refresh.
      let timer = 0;
      const resizeObserver = new ResizeObserver(() => {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => ScrollTrigger.refresh(), 150);
      });
      const main = document.querySelector("main");
      if (main) resizeObserver.observe(main);
      void document.fonts?.ready.then(() => ScrollTrigger.refresh());

      return () => {
        resizeObserver.disconnect();
        window.clearTimeout(timer);
        document.removeEventListener("click", onClick);
        window.removeEventListener("keydown", cancelAnchor, true);
        window.removeEventListener("pointerdown", cancelAnchor, true);
        trigger.kill();
        gsap.ticker.remove(tick);
        gsap.ticker.lagSmoothing(500, 33); // GSAP's default, restored when this owner lets go
        lenis.destroy();
        motion.path = null;
        motion.chapterStages = {};
        root.style.removeProperty("--rr-scene-opacity");
        root.style.removeProperty("--rr-glow-opacity");
        delete root.dataset.chapterPath;
        delete root.dataset.scrollTriggers;
        delete root.dataset.chapterScroll;
        delete root.dataset.chapterMeasured;
        delete root.dataset.choreo;
        requestFrame();
      };
    };

    // Choreography has its own matchMedia so it can be switched on and off with the scene kind.
    let choreo: gsap.MatchMedia | null = null;
    const syncChoreography = () => {
      const allowed = getSceneKind() === "hardware";
      if (allowed && !choreo) {
        choreo = gsap.matchMedia();
        choreo.add(CHOREO_QUERY, choreography);
      } else if (!allowed && choreo) {
        choreo.revert();
        choreo = null;
      }
    };
    syncChoreography();
    const offSceneKind = onSceneKindChange(syncChoreography);

    return () => {
      offSceneKind();
      choreo?.revert();
      mm.revert();
    };
  }, []);

  return null;
}
