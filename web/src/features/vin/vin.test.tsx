// PRD v2 F6 (A): input rules, check digit as a warning, decode states, confirm flow, VIN never persisted,
// and no fake VIN status text. 1HGCM82633A004352 is a widely published sample VIN with a valid check digit.
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { checkVin, decodeVin, expectedCheckDigit, interpret } from "./vin";
import { DECODE_NOTICE, HANDOFF_TEXT, VinCheck } from "./VinCheck";

const VIN = "1HGCM82633A004352";
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("input rules", () => {
  it("valid VIN; lowercase and surrounding spaces are normalised, nothing else", () => {
    expect(expectedCheckDigit(VIN)).toBe("3");
    expect(checkVin(`  ${VIN.toLowerCase()} `)).toEqual({ ok: true, vin: VIN, checkDigitWarning: null });
  });
  it.each([
    ["1HGCM82633A00435", /exactly 17 characters; this has 16/],
    ["1HGCM82633A0043521", /exactly 17 characters; this has 18/],
    ["1HGCM82633A0O4352", /never contain the letters I, O or Q \(found O\)/],
    ["IHGCM82633A004352", /found I/],
    ["1HGCM 82633A004352", /only letters and digits/],
    ["1HGCM-82633A00435", /only letters and digits/],
    ["", /Enter the 17-character VIN/],
  ])("%s is rejected with a specific message", (v, msg) => {
    const r = checkVin(v);
    expect(r.ok).toBe(false);
    expect(!r.ok && r.message).toMatch(msg);
  });
  it("a wrong check digit is a warning, not a rejection, and nothing is substituted", () => {
    const r = checkVin("1HGCM82643A004352");
    expect(r.ok && r.vin).toBe("1HGCM82643A004352");
    expect(r.ok && r.checkDigitWarning).toMatch(/other markets may still be valid/);
  });
});

describe("decode states", () => {
  it("success / partial / error / unsupported from vPIC fields", () => {
    expect(interpret({ Make: "HONDA", Model: "Accord", ModelYear: "2003", ErrorCode: "0" }).kind).toBe("success");
    expect(interpret({ Make: "HONDA", Model: "Accord", ModelYear: "2003", ErrorCode: "1", ErrorText: "1 - Check Digit" }).kind).toBe("partial");
    expect(interpret({ Make: "BMW", Model: "", ModelYear: "2011", ErrorCode: "6" }).kind).toBe("partial");
    expect(interpret({ Make: "", Model: "", ModelYear: "", ErrorCode: "5", ErrorText: "5 - VIN has errors" })).toEqual({
      kind: "error", errorCode: "5", errorText: "5 - VIN has errors" });
    expect(interpret({ ErrorCode: "7", ErrorText: "7 - not registered" }).kind).toBe("unsupported");
  });
  it("HTTP error and timeout → service unavailable", async () => {
    expect((await decodeVin(VIN, vi.fn().mockResolvedValue(new Response("x", { status: 503 })))).kind).toBe("unavailable");
    vi.useFakeTimers();
    const hang = vi.fn((_u: string, init?: RequestInit) =>
      new Promise<Response>((_r, reject) => init?.signal?.addEventListener("abort", () => reject(new Error("aborted")))));
    const p = decodeVin(VIN, hang as unknown as typeof fetch);
    await vi.advanceTimersByTimeAsync(10_000);
    expect((await p).kind).toBe("unavailable");
  });
});

function Where() {
  const l = useLocation();
  return <p data-testid="where">{l.pathname + l.search}</p>;
}
const show = (selected?: { make: string; model: string; model_year: number }) =>
  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<VinCheck selected={selected} />} />
        <Route path="/vehicle" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );
const vpic = (row: object) =>
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ Results: [row] }), { status: 200 })));

describe("VinCheck component", () => {
  it("notice before decoding; success needs confirmation; the VIN never reaches URL, storage or console", async () => {
    vpic({ Make: "HONDA", Model: "Accord", ModelYear: "2003", ErrorCode: "0" });
    const log = vi.spyOn(console, "log");
    const err = vi.spyOn(console, "error");
    show();
    expect(screen.getByTestId("vin-notice").textContent).toBe(DECODE_NOTICE);
    fireEvent.change(screen.getByLabelText(/Vehicle identification number/), { target: { value: VIN } });
    fireEvent.click(screen.getByRole("button", { name: "Decode with NHTSA" }));
    expect(await screen.findByText("Is this your vehicle?")).toBeTruthy();
    expect(screen.queryByTestId("where")).toBeNull(); // nothing happens without the confirmation
    fireEvent.click(screen.getByRole("button", { name: "Yes, show this vehicle" }));
    const where = (await screen.findByTestId("where")).textContent!;
    expect(where).toBe("/vehicle?make=HONDA&model=ACCORD&year=2003");
    expect(where).not.toContain(VIN);
    expect(JSON.stringify({ ...localStorage })).not.toContain(VIN);
    expect(JSON.stringify({ ...sessionStorage })).not.toContain(VIN);
    for (const spy of [log, err]) expect(JSON.stringify(spy.mock.calls)).not.toContain(VIN);
  });

  it("mismatch with the selected vehicle is shown separately", async () => {
    vpic({ Make: "HONDA", Model: "Accord", ModelYear: "2003", ErrorCode: "0" });
    show({ make: "EXAMPLE MOTORS", model: "ROADSTER", model_year: 2017 });
    fireEvent.change(screen.getByLabelText(/Vehicle identification number/), { target: { value: VIN } });
    fireEvent.click(screen.getByRole("button", { name: "Decode with NHTSA" }));
    expect((await screen.findByTestId("vin-mismatch")).textContent).toMatch(/not the 2017 EXAMPLE MOTORS ROADSTER/);
  });

  it.each([
    [{ Make: "", Model: "", ModelYear: "", ErrorCode: "5", ErrorText: "5 - VIN has errors" }, "vin-error"],
    [{ Make: "BMW", Model: "", ModelYear: "2011", ErrorCode: "6", ErrorText: "6 - Incomplete VIN" }, "vin-partial"],
    [{ ErrorCode: "7", ErrorText: "7 - not registered" }, "vin-unsupported"],
  ])("decode state %#", async (row, testId) => {
    vpic(row);
    show();
    fireEvent.change(screen.getByLabelText(/Vehicle identification number/), { target: { value: VIN } });
    fireEvent.click(screen.getByRole("button", { name: "Decode with NHTSA" }));
    expect(await screen.findByTestId(testId)).toBeTruthy();
  });

  it("official handoff always; copy with a manual fallback; no fake status words", async () => {
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText: vi.fn().mockRejectedValue(new Error("denied")) } });
    const { container } = show();
    const handoff = screen.getByTestId("vin-handoff");
    expect(handoff.textContent).toContain(HANDOFF_TEXT);
    const link = screen.getByRole("link", { name: "Check open recalls on NHTSA" });
    expect([link.getAttribute("href"), link.getAttribute("target"), link.getAttribute("rel")]).toEqual([
      "https://www.nhtsa.gov/recalls", "_blank", "noopener noreferrer"]);
    fireEvent.change(screen.getByLabelText(/Vehicle identification number/), { target: { value: VIN } });
    fireEvent.click(screen.getByRole("button", { name: "Copy VIN" }));
    expect(((await screen.findByLabelText("VIN to copy")) as HTMLInputElement).value).toBe(VIN);
    const text = container.textContent!;
    for (const bad of [/0 recalls/i, /all clear/i, /\bchecked\b/i, /\brepaired\b/i, /no open recalls/i]) {
      expect(text).not.toMatch(bad);
    }
  });
});
