// Owner: C. Introduction. In the `wide` layout (globals.css: ≥ 1024 px, or landscape-shaped ≥ 560 px,
// or two horizontal foldable segments) the grid is ~42% copy / ~58% vehicle stage; otherwise the stage
// sits above the copy. The car itself is drawn by the fixed background SceneLayer, which measures the
// visible [data-scene-stage] box and frames the car inside it (scene/stage.ts).
import type { CSSProperties } from "react";
import { HERO } from "@/content/copy";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

/** The 3D (or static) car is generic; this label says so wherever it is shown. */
function IllustrativeLabel({ className }: { className: string }) {
  return (
    <p
      className={
        "w-fit rounded-full border border-line-strong bg-graphite/70 px-3.5 py-1 text-xs tracking-[0.06em] text-muted backdrop-blur-sm " +
        className
      }
    >
      {HERO.vehicleLabel}
    </p>
  );
}

export function Hero() {
  return (
    <section
      id={SECTION_IDS.top}
      aria-labelledby="hero-title"
      className="rr-hero-grid safe-px mx-auto grid min-h-[calc(100svh-4rem)] max-w-[90rem] content-center items-center gap-x-10 gap-y-4 py-10 wide:grid-cols-[42fr_58fr] wide:py-16"
    >
      {/* Narrow layouts: the stage above the copy (height follows the small viewport, within limits). */}
      <div aria-hidden="true" data-scene-stage className="h-[clamp(9rem,30svh,20rem)] wide:hidden" />
      <IllustrativeLabel className="-mt-2 justify-self-center wide:hidden" />
      {/* Opaque on narrow layouts so light text never scrolls over the silver bodywork. */}
      <div className="rr-hero-copy @container bg-graphite wide:bg-transparent">
        <p className="rr-eyebrow rr-rise flex items-center gap-3">
          <span aria-hidden="true" className="h-px w-8 bg-champagne/60" />
          {HERO.eyebrow}
        </p>
        {/* Sized from this column (cqi), so the line breaks are the same at every width: in Space Grotesk
            500 "The available" is 5.81 em and the whole second line 10.37 em (measured), so at 15 cqi the
            second line always breaks once, after "available" (a three-line stack, never word by word).
            The second line is lighter and pearl rather than italic (Space Grotesk has no true italic).
            At extreme text zoom, overflow-wrap lets a long word break instead of overflowing the column. */}
        <h1 id="hero-title" className="rr-display mt-5 text-[clamp(2.25rem,15cqi,7rem)] text-ink [overflow-wrap:anywhere]">
          {HERO.titleLines.map((line, i) => (
            <span key={line} className={`rr-rise block ${i === 0 ? "" : "font-light text-pearl"}`} style={{ "--rr-i": i + 1 } as CSSProperties}>
              {line}
            </span>
          ))}
        </h1>
        <p className="rr-rise mt-7 max-w-md text-lg leading-relaxed text-muted sm:text-xl" style={{ "--rr-i": 3 } as CSSProperties}>
          {HERO.lede}
        </p>
        <div className="rr-rise mt-9 flex flex-wrap items-center gap-x-3 gap-y-3 wide:mt-11" style={{ "--rr-i": 4 } as CSSProperties}>
          <SmartLink to={DESTINATIONS.vehicleSearch} className="rr-btn rr-btn-primary min-h-12 px-6 text-base">
            {HERO.primaryAction}
          </SmartLink>
          <a href={`#${SECTION_IDS.howItWorks}`} className="rr-btn rr-btn-ghost min-h-12 px-6 text-base">
            {HERO.secondaryAction}
            <span aria-hidden="true" className="text-muted">
              ↓
            </span>
          </a>
        </div>
      </div>
      {/* Wide layouts: the stage is the right column. On short screens (≤ 500 px tall) the copy column can
          be taller than the viewport, so the stage aligns to the top instead of the row centre. */}
      <div
        data-scene-stage
        className="relative hidden aspect-[16/10] max-h-[70svh] w-full wide:block [@media(max-height:500px)]:self-start"
      >
        <IllustrativeLabel className="absolute -bottom-4 left-1/2 -translate-x-1/2" />
      </div>
    </section>
  );
}
