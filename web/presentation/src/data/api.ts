"use client";
// Owner: C. Read-only client for the product API (docs/CONTRACTS.md §6). Same origin in production
// (/observatory/ is served next to /api/*); NEXT_PUBLIC_RR_APP_ORIGIN points at another origin in dev.
// Every call has a timeout, checks that the response is JSON, and validates the fields the
// presentation reads, so a malformed or unexpected payload becomes an error state, never invented data.
import type { HeroPointer, Replay, VehicleResponse } from "@/contracts.gen";

const ORIGIN = (process.env.NEXT_PUBLIC_RR_APP_ORIGIN ?? "").replace(/\/+$/, "");
export const API_TIMEOUT_MS = 8000;

export type ApiFailureKind = "unavailable" | "not_found" | "bad_request" | "server" | "network" | "timeout" | "malformed";
export type ApiFailure = { kind: ApiFailureKind; status: number | null; message: string };
export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ApiFailure };

type Guard<T> = (value: unknown) => value is T;

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const isStr = (v: unknown): v is string => typeof v === "string";

function isProvenance(v: unknown): boolean {
  return isObj(v) && isStr(v.data_label) && (v.data_as_of === null || isStr(v.data_as_of));
}

function isVehicleKey(v: unknown): boolean {
  return isObj(v) && isStr(v.make) && isStr(v.model) && typeof v.model_year === "number";
}

export const isHero: Guard<HeroPointer> = (v): v is HeroPointer => isObj(v) && isStr(v.episode_id) && isProvenance(v.provenance);

export const isReplay: Guard<Replay> = (v): v is Replay =>
  isObj(v) && isStr(v.episode_id) && isStr(v.group_id) && isStr(v.comp_system) && isVehicleKey(v.vehicle) && isProvenance(v.provenance);

export const isVehicle: Guard<VehicleResponse> = (v): v is VehicleResponse =>
  isObj(v) &&
  isVehicleKey(v.vehicle) &&
  isProvenance(v.provenance) &&
  typeof v.distinct_complaints === "number" &&
  isStr(v.note) &&
  Array.isArray(v.components) &&
  v.components.every(
    (c) => isObj(c) && isObj(c.group) && isStr(c.group.group_id) && isStr(c.group.comp_system) && typeof c.group.distinct_complaints === "number" && Array.isArray(c.episodes),
  ) &&
  Array.isArray(v.recall_campaigns) &&
  v.recall_campaigns.every((r) => isObj(r) && isStr(r.campno) && isStr(r.component) && (r.report_date === null || isStr(r.report_date)));

function failureFor(status: number, body: unknown): ApiFailure {
  const message = isObj(body) && isObj(body.error) && isStr(body.error.message) ? body.error.message : `Request failed (${status}).`;
  if (status === 404) return { kind: "not_found", status, message };
  if (status === 400) return { kind: "bad_request", status, message };
  if (status === 503) return { kind: "unavailable", status, message };
  return { kind: "server", status, message };
}

export async function getJson<T>(path: string, guard: Guard<T>, signal?: AbortSignal): Promise<ApiResult<T>> {
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(), API_TIMEOUT_MS);
  const onOuterAbort = () => timeout.abort();
  signal?.addEventListener("abort", onOuterAbort);
  try {
    const res = await fetch(`${ORIGIN}${path}`, { headers: { Accept: "application/json" }, signal: timeout.signal });
    const isJson = (res.headers.get("content-type") ?? "").includes("application/json");
    const body: unknown = isJson ? await res.json().catch(() => undefined) : undefined;
    if (!res.ok) return { ok: false, error: failureFor(res.status, body) };
    if (!isJson || body === undefined) return { ok: false, error: { kind: "malformed", status: res.status, message: "The data service returned something that is not data." } };
    if (!guard(body)) return { ok: false, error: { kind: "malformed", status: res.status, message: "The data did not have the expected shape." } };
    return { ok: true, data: body };
  } catch {
    if (signal?.aborted) return { ok: false, error: { kind: "network", status: null, message: "Cancelled." } };
    if (timeout.signal.aborted) return { ok: false, error: { kind: "timeout", status: null, message: "The data service took too long to answer." } };
    return { ok: false, error: { kind: "network", status: null, message: "The data service cannot be reached." } };
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onOuterAbort);
  }
}

export const api = {
  hero: (signal?: AbortSignal) => getJson("/api/hero", isHero, signal),
  replay: (episodeId: string, signal?: AbortSignal) => getJson(`/api/replay/${encodeURIComponent(episodeId)}`, isReplay, signal),
  vehicle: (make: string, model: string, year: number, signal?: AbortSignal) =>
    getJson(`/api/vehicle?${new URLSearchParams({ make, model, year: String(year) })}`, isVehicle, signal),
};
