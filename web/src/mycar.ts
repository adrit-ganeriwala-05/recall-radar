// Owner: C. PRD v2 F4: make/model/year only, under one key; every storage access is guarded.
export const MYCAR_KEY = "rr.mycar.v1";
export type MyCar = { v: 1; make: string; model: string; year: number };
export type ReadResult = { car: MyCar | null; problem: string | null };

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function readMyCar(): ReadResult {
  let raw: string | null;
  try {
    const s = storage();
    if (!s) return { car: null, problem: null };
    raw = s.getItem(MYCAR_KEY);
  } catch {
    return { car: null, problem: "Your saved car couldn't be read in this browser." };
  }
  if (raw === null) return { car: null, problem: null };
  try {
    const o = JSON.parse(raw) as Record<string, unknown>;
    if (
      o &&
      o.v === 1 &&
      typeof o.make === "string" &&
      o.make &&
      typeof o.model === "string" &&
      o.model &&
      typeof o.year === "number" &&
      Number.isInteger(o.year)
    ) {
      return { car: { v: 1, make: o.make, model: o.model, year: o.year }, problem: null };
    }
  } catch {
    /* fall through */
  }
  return { car: null, problem: "Your saved car couldn't be read, so it was ignored." };
}

/** "saved" only when the value read back equals what was written. */
export function saveMyCar(make: string, model: string, year: number): "saved" | "failed" {
  const value = JSON.stringify({ v: 1, make, model, year } satisfies MyCar);
  try {
    const s = storage();
    if (!s) return "failed";
    s.setItem(MYCAR_KEY, value);
    return s.getItem(MYCAR_KEY) === value ? "saved" : "failed";
  } catch {
    return "failed";
  }
}

export function forgetMyCar(): boolean {
  try {
    storage()?.removeItem(MYCAR_KEY); // never clear(): other keys are not ours
    return true;
  } catch {
    return false;
  }
}

export function sameCar(car: MyCar | null, make: string, model: string, year: number): boolean {
  return !!car && car.make === make && car.model === model && car.year === year;
}
