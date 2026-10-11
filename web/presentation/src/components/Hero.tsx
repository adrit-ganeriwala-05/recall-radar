// Owner: C. Introduction. Wide grid is ~42% copy / ~58% vehicle composition. The car itself is drawn
// by the fixed background SceneLayer (motionState COMPOSITIONS anchor it in the right column wide, and
// above the copy narrow); this section only reserves that space and carries the DOM label.
import { HERO } from "@/content/copy";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

/** The 3D (or static) car is generic; this label says so wherever it is shown. */
function IllustrativeLabel({ className }: { className: string }) {
  return (
    <p className={"w-fit rounded-md border border-line bg-graphite/70 px-3 py-1 text-sm text-muted " + className}>
      {HERO.vehicleLabel}
    </p>
  );
}

export function Hero() {
  return (
    <section
      id={SECTION_IDS.top}
      aria-labelledby="hero-title"
      className="mx-auto grid min-h-[calc(100dvh-4rem)] max-w-[90rem] items-center gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[42fr_58fr]"
    >
      {/* @container: the heading is sized from this column's width (cqi), so the two authored lines
          never break word-by-word inside the 42% column. "The available evidence." is ~10.3em wide. */}
      {/* Narrow screens: reserved area for the car above the copy (narrow composition anchor y = 0.3). */}
      <div aria-hidden="true" className="h-[20svh] lg:hidden" />
      <IllustrativeLabel className="-mt-6 justify-self-center lg:hidden" />
      {/* Opaque on narrow screens so light text never scrolls over the silver bodywork. */}
      <div className="@container bg-graphite lg:bg-transparent">
        <h1
          id="hero-title"
          className="text-[clamp(2.25rem,9.4cqi,7rem)] font-medium leading-[1.04] tracking-[-0.03em] text-ink"
        >
          {HERO.titleLines.map((line) => (
            <span key={line} className="block">
              {line}
            </span>
          ))}
        </h1>
        <p className="mt-6 max-w-md text-lg leading-relaxed text-muted sm:text-xl">{HERO.lede}</p>
        <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-4">
          <SmartLink
            to={DESTINATIONS.vehicleSearch}
            className="inline-flex min-h-12 items-center rounded-md bg-cobalt-strong px-6 text-base font-medium text-ink transition-colors hover:bg-cobalt-strong/85"
          >
            {HERO.primaryAction}
          </SmartLink>
          <a
            href={`#${SECTION_IDS.howItWorks}`}
            className="inline-flex min-h-12 items-center gap-2 rounded px-1 text-base text-ink/90 transition-colors hover:text-ink"
          >
            {HERO.secondaryAction}
            <span aria-hidden="true">↓</span>
          </a>
        </div>
      </div>
      <div className="relative hidden aspect-[16/10] w-full lg:block">
        <IllustrativeLabel className="absolute -bottom-4 left-1/2 -translate-x-1/2" />
      </div>
    </section>
  );
}
