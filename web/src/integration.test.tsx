// PRD v2 integration (C owns routes/pages): F5 /report, F8 /vehicle/report, F6 /vin + landing, entry links.
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import report from "../../contracts/fixtures/api/report.json";
import App from "./App";

const at = (path: string) => render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);

describe("v2 routes and entry points", () => {
  it("header links: Check by VIN and Report a problem (no vehicle)", () => {
    at("/results");
    const nav = screen.getByRole("navigation", { name: "Main" });
    expect(within(nav).getByRole("link", { name: "Check by VIN" }).getAttribute("href")).toBe("/vin");
    expect(within(nav).getByRole("link", { name: "Report a problem" }).getAttribute("href")).toBe("/report");
  });
  it("/report, /vin and /vehicle/report render their components", async () => {
    const { unmount } = at("/report");
    expect(await screen.findByText(/This draft is not saved if you close or refresh the page/)).toBeTruthy();
    unmount();
    const u2 = at("/vin");
    expect(screen.getByText("Decoding sends this VIN to NHTSA's vPIC service.")).toBeTruthy();
    u2.unmount();
    // D's F8 route fetches /api/report itself (no fixture client), so stub it with the contract fixture
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(report), { status: 200, headers: { "content-type": "application/json" } })));
    at("/vehicle/report?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017");
    expect((await screen.findAllByText("Used-car complaint and recall summary")).length).toBeGreaterThan(0);
    vi.unstubAllGlobals();
  });
  it("vehicle page links to the summary and a prefilled report; landing shows Check by VIN", async () => {
    const { unmount } = at("/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017");
    expect((await screen.findByRole("link", { name: "Used-car complaint and recall summary" })).getAttribute("href"))
      .toBe("/vehicle/report?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017");
    expect(screen.getByRole("link", { name: "Report a problem with this vehicle" }).getAttribute("href"))
      .toBe("/report?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017");
    unmount();
    at("/?change=1");
    expect(await screen.findByTestId("vin-check")).toBeTruthy();
  });
});
