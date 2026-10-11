// Owner: C. Compact header (z-30 in the presentation stacking order). Every item goes to a real
// destination: a product route or a section rendered on this page.
import { NAV } from "@/content/copy";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

const linkClass =
  "rounded px-1 py-2 text-[15px] text-ink/90 transition-colors hover:text-ink focus-visible:text-ink";

function RadarMark() {
  // Decorative brand mark (authored SVG, no external asset).
  return (
    <svg aria-hidden="true" viewBox="0 0 32 32" className="h-7 w-7 text-cobalt">
      <circle cx="16" cy="16" r="14.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="16" cy="16" r="9.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="16" cy="16" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-graphite/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-[90rem] flex-wrap items-center justify-between gap-x-6 gap-y-2 px-5 py-3 sm:px-8">
        <a href={`#${SECTION_IDS.top}`} className="flex items-center gap-2.5 rounded text-lg font-medium tracking-tight">
          <RadarMark />
          Recall Radar
        </a>
        <nav aria-label="Presentation">
          <ul className="flex flex-wrap items-center gap-x-5 gap-y-1">
            <li>
              <SmartLink to={DESTINATIONS.vehicleSearch} className={linkClass}>
                {NAV.explore}
              </SmartLink>
            </li>
            <li>
              <a href={`#${SECTION_IDS.howItWorks}`} className={linkClass}>
                {NAV.howItWorks}
              </a>
            </li>
            <li>
              <SmartLink to={DESTINATIONS.results} className={linkClass}>
                {NAV.evidence}
              </SmartLink>
            </li>
            <li>
              <SmartLink
                to={DESTINATIONS.vehicleSearch}
                className="rounded-md border border-line px-3 py-1.5 text-[15px] font-medium text-ink transition-colors hover:border-cobalt"
              >
                {NAV.openApp}
              </SmartLink>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}
