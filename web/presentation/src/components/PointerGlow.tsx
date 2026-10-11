"use client";
// Owner: C. Cursor-reactive light on cards: one passive, delegated pointermove listener writes the
// pointer position into --mx / --my on the card under it, and CSS (`rr-card` in globals.css) draws a
// soft edge light and inner glow there. Mouse and pen with hover only; touch never sees it. Writes two
// custom properties per move and no layout, so it costs nothing measurable; it never moves content.
import { useEffect } from "react";

export function PointerGlow() {
  useEffect(() => {
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)");
    const onMove = (e: PointerEvent) => {
      if (!fine.matches || e.pointerType === "touch") return;
      const card = (e.target as Element | null)?.closest?.<HTMLElement>(".rr-card");
      if (!card) return;
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${e.clientX - r.left}px`);
      card.style.setProperty("--my", `${e.clientY - r.top}px`);
    };
    document.addEventListener("pointermove", onMove, { passive: true });
    return () => document.removeEventListener("pointermove", onMove);
  }, []);
  return null;
}
