// Owner: C. One function per API endpoint; each returns typed data or a typed ErrorResponse.
// Mode comes from VITE_API_MODE:
//   fixture  -> bundles contracts/fixtures/api/*.json (no network at all)
//   live     -> calls /api; when the API is unreachable, falls back to /demo/*.json (the
//               bundled exports/demo copy) for the endpoints that have an offline file.
import type {
  ErrorCode,
  ErrorResponse,
  EvaluationSummary,
  HeroPointer,
  IssueResponse,
  ListResponse,
  MetaResponse,
  Replay,
  VehicleResponse,
} from "../contracts.gen";

export type ApiMode = "fixture" | "live";
export type Source = "fixture" | "live" | "offline";
export type Period = "development" | "held_out";

export type ApiResult<T> =
  | { ok: true; data: T; source: Source }
  | { ok: false; error: ErrorResponse; status: number };

export function apiMode(): ApiMode {
  return import.meta.env.VITE_API_MODE === "fixture" ? "fixture" : "live";
}

// ----------------------------------------------------------------------------- endpoints
// Paths per docs/CONTRACTS.md §6. Change them here only.
export const ENDPOINTS = {
  meta: () => "/api/meta",
  makes: () => "/api/makes",
  models: (make: string) => `/api/models?${qs({ make })}`,
  years: (make: string, model: string) => `/api/years?${qs({ make, model })}`,
  vehicle: (make: string, model: string, year: number) =>
    `/api/vehicle?${qs({ make, model, year: String(year) })}`,
  issue: (groupId: string, page: number, episodeId?: string) =>
    `/api/issue/${encodeURIComponent(groupId)}?${qs({ page: String(page), ...(episodeId ? { episode_id: episodeId } : {}) })}`,
  replay: (episodeId: string) => `/api/replay/${encodeURIComponent(episodeId)}`,
  results: (period: Period) => `/api/results?${qs({ period })}`,
  resultsCsv: (period: Period) => `/api/export/results.csv?${qs({ period })}`,
  hero: () => "/api/hero",
};

// Files in exports/demo (CONTRACTS.md §7; copied to dist/demo at build) used when the API is
// unreachable. There is no offline meta file: the header then says the data service is offline.
export const OFFLINE = {
  replay: (episodeId: string) => [`/demo/replays/${episodeId}.json`],
  results: (period: Period) => [`/demo/results_${period}.json`],
  resultsCsv: () => "/demo/results.csv",
  hero: () => ["/demo/hero.json"],
};

function qs(params: Record<string, string>): string {
  return new URLSearchParams(params).toString();
}

// ----------------------------------------------------------------------------- fixtures

// Lazy, and only in a fixture build: Vite replaces VITE_API_MODE at build time, so a live build drops
// this branch and ships no synthetic fixture JSON at all.
const FIXTURES: Record<string, () => Promise<unknown>> =
  import.meta.env.VITE_API_MODE === "fixture"
    ? import.meta.glob("../../../contracts/fixtures/api/*.json", { import: "default" })
    : {};

async function fixture<T>(name: string): Promise<T | undefined> {
  const key = Object.keys(FIXTURES).find((k) => k.endsWith(`/${name}`));
  return key ? ((await FIXTURES[key]()) as T) : undefined;
}

export function errorBody(code: ErrorCode, message: string, detail: Record<string, string> | null = null): ErrorResponse {
  return { error: { code, message, detail } };
}

const STATUS_FOR: Record<ErrorCode, number> = {
  invalid_parameter: 400,
  not_found: 404,
  unavailable: 503,
  internal: 500,
};

function fail<T>(err: ErrorResponse): ApiResult<T> {
  return { ok: false, error: err, status: STATUS_FOR[err.error.code] };
}

async function fromFixture<T>(name: string, accept: (data: T) => boolean = () => true): Promise<ApiResult<T>> {
  const data = await fixture<T>(name);
  if (data !== undefined && accept(data)) return { ok: true, data, source: "fixture" };
  const nf = await fixture<ErrorResponse>("error_not_found.json");
  return fail(nf ?? errorBody("not_found", "Not found in the test data."));
}

// ----------------------------------------------------------------------------- live

function isErrorResponse(x: unknown): x is ErrorResponse {
  return typeof x === "object" && x !== null && "error" in x && typeof (x as ErrorResponse).error?.code === "string";
}

async function getJson<T>(path: string, offline: string[] = []): Promise<ApiResult<T>> {
  let unreachable = false;
  let res: Response | undefined;
  try {
    res = await fetch(path, { headers: { Accept: "application/json" } });
  } catch {
    unreachable = true;
  }
  if (res && res.ok) return { ok: true, data: (await res.json()) as T, source: "live" };
  // 502/503/504: proxy cannot reach the API, or the API has no data built yet.
  if (!res || res.status >= 502) unreachable = true;

  if (unreachable) {
    for (const file of offline) {
      try {
        const o = await fetch(file, { headers: { Accept: "application/json" } });
        const type = o.headers.get("content-type") ?? "";
        if (o.ok && type.includes("json")) return { ok: true, data: (await o.json()) as T, source: "offline" };
      } catch {
        /* try next candidate */
      }
    }
  }

  if (res) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      /* not JSON */
    }
    if (isErrorResponse(body)) return { ok: false, error: body, status: res.status };
    if (res.status < 500) return { ok: false, error: errorBody("invalid_parameter", `Request failed (${res.status}).`), status: res.status };
  }
  return { ok: false, error: errorBody("unavailable", "The data service cannot be reached."), status: 503 };
}

// ----------------------------------------------------------------------------- API

export async function getMeta(): Promise<ApiResult<MetaResponse>> {
  if (apiMode() === "fixture") return fromFixture("meta.json");
  return getJson(ENDPOINTS.meta());
}

export async function getMakes(): Promise<ApiResult<ListResponse>> {
  if (apiMode() === "fixture") return fromFixture("makes.json");
  return getJson(ENDPOINTS.makes());
}

export async function getModels(make: string): Promise<ApiResult<ListResponse>> {
  if (apiMode() === "fixture") return fromFixture("models.json");
  return getJson(ENDPOINTS.models(make));
}

export async function getYears(make: string, model: string): Promise<ApiResult<ListResponse>> {
  if (apiMode() === "fixture") return fromFixture("years.json");
  return getJson(ENDPOINTS.years(make, model));
}

export async function getVehicle(make: string, model: string, year: number): Promise<ApiResult<VehicleResponse>> {
  if (apiMode() === "fixture") {
    return fromFixture<VehicleResponse>(
      "vehicle.json",
      (v) => v.vehicle.make === make && v.vehicle.model === model && v.vehicle.model_year === year,
    );
  }
  return getJson(ENDPOINTS.vehicle(make, model, year));
}

/** `episodeId` limits evidence to that episode's alert window (server side; fixtures ignore it). */
export async function getIssue(groupId: string, page = 1, episodeId?: string): Promise<ApiResult<IssueResponse>> {
  if (apiMode() === "fixture") {
    return fromFixture<IssueResponse>("issue.json", (i) => i.group.group_id === groupId && i.evidence.page === page);
  }
  return getJson(ENDPOINTS.issue(groupId, page, episodeId));
}

export async function getReplay(episodeId: string): Promise<ApiResult<Replay>> {
  if (apiMode() === "fixture") return fromFixture(`replay_${episodeId}.json`);
  return getJson(ENDPOINTS.replay(episodeId), OFFLINE.replay(episodeId));
}

export async function getResults(period: Period): Promise<ApiResult<EvaluationSummary>> {
  if (apiMode() === "fixture") return fromFixture(`results_${period}.json`);
  return getJson(ENDPOINTS.results(period), OFFLINE.results(period));
}

/** Where the results CSV for the data being shown can be downloaded; null for fixtures. */
export function resultsCsvUrl(period: Period, source: Source): string | null {
  if (source === "live") return ENDPOINTS.resultsCsv(period);
  if (source === "offline") return OFFLINE.resultsCsv();
  return null;
}

export async function getHero(): Promise<ApiResult<HeroPointer>> {
  if (apiMode() === "fixture") return fromFixture("hero.json");
  return getJson(ENDPOINTS.hero(), OFFLINE.hero());
}
