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

/** In-page section ids. Phase 1 renders only `top` and `how-it-works`. */
export const SECTION_IDS = {
  top: "top",
  howItWorks: "how-it-works",
} as const;
