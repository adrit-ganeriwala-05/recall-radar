// PRD v2 F7 UI: examples, browser-only search (no request carries the query), no storage/URL, no-match text, clear.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { EXAMPLES, METHOD_LINE, NO_MATCH, SymptomSearch } from "./components/SymptomSearch";

const V = { make: "EXAMPLE MOTORS", model: "ROADSTER", model_year: 2017 };
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });

function Where() {
  const l = useLocation();
  return <p data-testid="url">{l.pathname + l.search + l.hash}</p>;
}
const show = () =>
  render(
    <MemoryRouter initialEntries={["/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017"]}>
      <Routes>
        <Route path="/vehicle" element={<><SymptomSearch vehicle={V} reportHref="/report-problem" /><Where /></>} />
      </Routes>
    </MemoryRouter>,
  );
async function type(text: string) {
  fireEvent.change(screen.getByLabelText("Describe the problem in your own words"), { target: { value: text } });
  await act(async () => { await new Promise((r) => setTimeout(r, 300)); }); // debounce 250 ms
}

describe("symptom search UI", () => {
  it("offers the four PRD examples as chips", async () => {
    show();
    await screen.findByRole("button", { name: EXAMPLES[0] });
    expect(EXAMPLES).toEqual(["door doesn't lock properly", "brakes make noise", "steering wheel shakes", "engine stalls while driving"]);
    for (const ex of EXAMPLES) expect(screen.getByRole("button", { name: ex })).toBeTruthy();
  });

  it("finds the fixture's brake-noise complaint and keeps brake failure apart", async () => {
    show();
    await screen.findByRole("button", { name: EXAMPLES[1] });
    await type("brakes make noise");
    expect(screen.getByText("Similar reported symptoms")).toBeTruthy();
    expect(screen.getByTestId("symptom-method").textContent).toBe(METHOD_LINE);
    const hits = screen.getAllByTestId("symptom-hit");
    expect(hits.map((h) => h.textContent)).toEqual([expect.stringContaining("Complaint 10000102")]);
    expect(screen.getByTestId("symptom-count").textContent).toBe("1 similar complaint.");
    expect(hits[0].querySelector('a[href^="/issue/"]')).toBeTruthy();
  });

  it("the typed text never reaches a request, storage or the URL", async () => {
    const spy = vi.spyOn(globalThis, "fetch");
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    show();
    await screen.findByRole("button", { name: EXAMPLES[0] });
    await type("ZZQ-SYNTH-7741 grinding brakes");
    for (const call of spy.mock.calls) expect(String(call[0])).not.toMatch(/ZZQ|grinding/i);
    expect(setItem).not.toHaveBeenCalled();
    expect(screen.getByTestId("url").textContent).not.toMatch(/ZZQ|grinding/i);
  });

  it("no match says so and offers Report a problem; Clear empties the search", async () => {
    show();
    await screen.findByRole("button", { name: EXAMPLES[0] });
    await type("sunroof leaks");
    expect(screen.getByTestId("symptom-none").textContent).toContain(NO_MATCH);
    expect(screen.getByRole("link", { name: "Report a problem" }).getAttribute("href")).toBe("/report-problem");
    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect((screen.getByLabelText("Describe the problem in your own words") as HTMLInputElement).value).toBe("");
    expect(screen.queryByText("Similar reported symptoms")).toBeNull();
  });
});
