// Owner: C. Compact header (z-30 in the presentation stacking order). Every item goes to a real
// destination: a section on this page (Explore, How it works, Evidence) or the product (Open app).
// Targets are at least 44 px tall.
// Sticky only where there is room (≥ 640 px wide and ≥ 500 px tall): on phones and short landscape
// screens a wrapped, sticky header would cover too much of the page, so it scrolls away instead.
import { NAV } from "@/content/copy";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

const linkClass =
  "inline-flex min-h-11 items-center rounded px-1.5 text-[14px] text-pearl transition-colors hover:text-ink focus-visible:text-ink sm:px-2.5 sm:text-[15px]";

function RadarMark() {
  // Decorative brand mark (authored SVG, no external asset).
  return (
    <svg aria-hidden="true" viewBox="0 0 32 32" className="h-7 w-7 shrink-0 text-cobalt">
      <circle cx="16" cy="16" r="14.5" fill="none" stroke="currentColor" strokeWidth="1.25" opacity="0.55" />
      <circle cx="16" cy="16" r="9.5" fill="none" stroke="currentColor" strokeWidth="1.25" opacity="0.8" />
      <circle cx="16" cy="16" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="16" cy="16" r="1.4" fill="currentColor" />
    </svg>
  );
}

export function SiteHeader() {
  return (
    <header className="relative top-0 z-30 bg-graphite/75 backdrop-blur-xl [@media(min-width:640px)_and_(min-height:500px)]:sticky">
      <a
        href="#main"
        className="sr-only rounded-full bg-cobalt-strong px-4 py-3 text-ink focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50"
      >
        Skip to content
      </a>
      <div className="safe-px mx-auto flex max-w-[90rem] flex-wrap items-center justify-between gap-x-6 gap-y-1 py-1.5 [padding-top:max(0.375rem,env(safe-area-inset-top))]">
        <a href={`#${SECTION_IDS.top}`} className="inline-flex min-h-11 items-center gap-2.5 rounded pr-1 text-lg font-medium tracking-tight">
          <RadarMark />
          Recall Radar
        </a>
        <nav aria-label="Presentation">
          <ul className="flex flex-wrap items-center gap-x-1 gap-y-0 sm:gap-x-2">
            {/* Below 360 px "Explore" is dropped to keep the header on two rows; the section is the next one
                after "How it works" and "Open app" reaches the same records in the app. */}
            <li className="hidden min-[360px]:block">
              <a href={`#${SECTION_IDS.explore}`} className={linkClass}>
                {NAV.explore}
              </a>
            </li>
            <li>
              <a href={`#${SECTION_IDS.howItWorks}`} className={linkClass}>
                {NAV.howItWorks}
              </a>
            </li>
            <li>
              <a href={`#${SECTION_IDS.evidence}`} className={linkClass}>
                {NAV.evidence}
              </a>
            </li>
            <li>
              <SmartLink to={DESTINATIONS.vehicleSearch} className="rr-btn rr-btn-ghost ml-1 min-h-11 min-w-11 px-3 text-[14px] sm:px-4 sm:text-[15px]">
                {NAV.openApp}
              </SmartLink>
            </li>
          </ul>
        </nav>
      </div>
      <div aria-hidden="true" className="rr-hairline absolute inset-x-0 bottom-0" />
      <div aria-hidden="true" className="rr-progress absolute bottom-0 left-0 h-px w-full" />
    </header>
  );
}
