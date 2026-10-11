// Owner: C. Every link out of the presentation goes through here.
// The presentation is served at /observatory/ on the same origin as the product (web/dist), so the
// product's own routes (web/src/App.tsx) are plain same-origin paths. For local development against
// the Vite dev server set NEXT_PUBLIC_RR_APP_ORIGIN, e.g. http://127.0.0.1:5173.
// Only routes that exist in the product today are listed; nothing here is a placeholder.

const APP_ORIGIN = (process.env.NEXT_PUBLIC_RR_APP_ORIGIN ?? "").replace(/\/+$/, "");

type AppPath = `/${string}`;

function appUrl(path: AppPath): string {
  return `${APP_ORIGIN}${path}`;
}

export type Destination = {
  href: string;
  /** true when the link leaves Recall Radar entirely (opens in a new tab). */
  external: boolean;
};

export const DESTINATIONS = {
  /** Product landing page: make → model → year selector (web/src/pages/SelectorPage.tsx). */
  vehicleSearch: { href: appUrl("/"), external: false },
  /** Product results page: development and held-out evaluation (web/src/pages/ResultsPage.tsx). */
  results: { href: appUrl("/results"), external: false },
  /** NHTSA's official recall lookup by VIN (CLAUDE.md §1: always offered for a specific car). */
  nhtsaRecalls: { href: "https://www.nhtsa.gov/recalls", external: true },
} as const satisfies Record<string, Destination>;

export type VehicleRef = { make: string; model: string; model_year: number };

const vehicleQuery = (v: VehicleRef) => new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year) }).toString();

/** Product routes that take parameters; built exactly like the product's own links (web/src). */
export const ROUTES = {
  /** Vehicle page (web/src/pages/VehiclePage.tsx). */
  vehicle: (v: VehicleRef): Destination => ({ href: appUrl(`/vehicle?${vehicleQuery(v)}`), external: false }),
  /** Issue page with the evidence list (web/src/pages/IssuePage.tsx). */
  issue: (groupId: string): Destination => ({ href: appUrl(`/issue/${encodeURIComponent(groupId)}`), external: false }),
  /** Month-by-month replay (web/src/pages/ReplayPage.tsx). */
  replay: (episodeId: string): Destination => ({ href: appUrl(`/replay/${encodeURIComponent(episodeId)}`), external: false }),
  /** F8 buyer report (buyerReportHref in web/src/features/buyer-report/BuyerReportRoute.tsx). */
  buyerReport: (v: VehicleRef): Destination => ({ href: appUrl(`/vehicle/report?${vehicleQuery(v)}`), external: false }),
  /** F5 report-a-problem helper (reportHref in web/src/features/report/ReportRoute.tsx). */
  reportProblem: (): Destination => ({ href: appUrl("/report"), external: false }),
  /** F6 VIN identification (web/src/features/vin). */
  vin: (): Destination => ({ href: appUrl("/vin"), external: false }),
};

/** In-page section ids, in page order. */
export const SECTION_IDS = {
  top: "top",
  howItWorks: "how-it-works",
  explore: "explore",
  record: "follow-the-record",
  official: "official-information",
  evidence: "evidence",
  continue: "continue",
} as const;
