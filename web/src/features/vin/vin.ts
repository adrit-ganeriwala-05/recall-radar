// Owner: A. PRD v2 F6: VIN input rules, check digit (warning only), and the user-initiated vPIC decode.
// The VIN lives only in component memory: never stored, put in a URL, logged or sent anywhere but vPIC.
export const VPIC_URL = (vin: string) =>
  `https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/${encodeURIComponent(vin)}?format=json`;
export const NHTSA_RECALLS_URL = "https://www.nhtsa.gov/recalls";
export const DECODE_TIMEOUT_MS = 10_000;

export type VinCheck =
  | { ok: true; vin: string; checkDigitWarning: string | null }
  | { ok: false; message: string };

const TRANSLIT: Record<string, number> = {
  A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8, J: 1, K: 2, L: 3, M: 4, N: 5, P: 7, R: 9,
  S: 2, T: 3, U: 4, V: 5, W: 6, X: 7, Y: 8, Z: 9,
}; // prettier-ignore
const WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2];

/** North American check digit (position 9); null if the VIN has characters that cannot be valued. */
export function expectedCheckDigit(vin: string): string | null {
  let sum = 0;
  for (let i = 0; i < 17; i++) {
    const ch = vin[i];
    const v = /\d/.test(ch) ? Number(ch) : TRANSLIT[ch];
    if (v === undefined) return null;
    sum += v * WEIGHTS[i];
  }
  const r = sum % 11;
  return r === 10 ? "X" : String(r);
}

/** Trim + uppercase only; no other character is changed or substituted. */
export function checkVin(input: string): VinCheck {
  const vin = input.trim().toUpperCase();
  if (vin.length === 0) return { ok: false, message: "Enter the 17-character VIN." };
  if (!/^[A-Z0-9]+$/.test(vin)) return { ok: false, message: "A VIN has only letters and digits — no spaces or symbols." };
  const ioq = [...new Set(vin.match(/[IOQ]/g) ?? [])];
  if (ioq.length) {
    return {
      ok: false,
      message: `VINs never contain the letters I, O or Q (found ${ioq.join(", ")}). Check for the digits 1 or 0.`,
    };
  }
  if (vin.length !== 17) return { ok: false, message: `A VIN has exactly 17 characters; this has ${vin.length}.` };
  const want = expectedCheckDigit(vin);
  const checkDigitWarning =
    want !== null && vin[8] !== want
      ? "The check digit (9th character) does not match the North American formula. Vehicles built for other markets may still be valid; check the VIN on the car or its title."
      : null;
  return { ok: true, vin, checkDigitWarning };
}

export type DecodeState =
  | { kind: "success"; make: string; model: string; year: number; errorText: string | null }
  | { kind: "partial"; make: string | null; model: string | null; year: number | null; errorText: string }
  | { kind: "error"; errorCode: string; errorText: string }
  | { kind: "unsupported"; errorText: string }
  | { kind: "unavailable"; detail: string };

type VpicRow = { Make?: string; Model?: string; ModelYear?: string; ErrorCode?: string; ErrorText?: string };

/** vPIC ErrorCode "0" = decoded cleanly; codes are a comma list. Make/model/year missing → partial or error. */
export function interpret(row: VpicRow | undefined): DecodeState {
  if (!row) return { kind: "unavailable", detail: "NHTSA's service returned no result." };
  const codes = String(row.ErrorCode ?? "").split(",").map((c) => c.trim()).filter(Boolean);
  const text = String(row.ErrorText ?? "").trim();
  const make = (row.Make ?? "").trim() || null;
  const model = (row.Model ?? "").trim() || null;
  const yearN = Number(row.ModelYear);
  const year = Number.isInteger(yearN) && yearN > 1900 ? yearN : null;
  if (codes.includes("7")) return { kind: "unsupported", errorText: text }; // manufacturer not registered for US sale
  if (make && model && year) {
    return codes.every((c) => c === "0")
      ? { kind: "success", make, model, year, errorText: null }
      : { kind: "partial", make, model, year, errorText: text };
  }
  if (make || model || year) return { kind: "partial", make, model, year, errorText: text || "Some fields are missing." };
  return { kind: "error", errorCode: codes.join(", ") || "unknown", errorText: text || "NHTSA could not decode this VIN." };
}

export async function decodeVin(vin: string, fetchImpl: typeof fetch = fetch): Promise<DecodeState> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), DECODE_TIMEOUT_MS);
  try {
    const r = await fetchImpl(VPIC_URL(vin), { signal: ctrl.signal, credentials: "omit", referrerPolicy: "no-referrer" });
    if (!r.ok) return { kind: "unavailable", detail: `NHTSA's service answered ${r.status}.` };
    const body = (await r.json()) as { Results?: VpicRow[] };
    return interpret(body.Results?.[0]);
  } catch {
    return { kind: "unavailable", detail: "NHTSA's service could not be reached or did not answer in time." };
  } finally {
    clearTimeout(timer);
  }
}
