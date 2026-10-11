// Owner: C. Introduction. Desktop grid is ~42% copy / ~58% vehicle composition; the right column is
// reserved for the vehicle scene, which renders in the separate background SceneLayer (Phase 2) and
// therefore never sits inside this text flow. Until then it holds only a quiet studio-floor gradient.
import { HERO } from "@/content/copy";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

export function Hero() {
  return (
    <section
      id={SECTION_IDS.top}
      aria-labelledby="hero-title"
      className="mx-auto grid min-h-[calc(100dvh-4rem)] max-w-[90rem] items-center gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[42fr_58fr]"
    >
      {/* @container: the heading is sized from this column's width (cqi), so the two authored lines
          never break word-by-word inside the 42% column. "The available evidence." is ~10.3em wide. */}
      <div className="@container">
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
      <div
        aria-hidden="true"
        className="hidden aspect-[16/10] w-full rounded-[2rem] bg-[radial-gradient(60%_45%_at_55%_75%,rgb(245_242_235/0.07),transparent_70%)] lg:block"
      />
    </section>
  );
}
