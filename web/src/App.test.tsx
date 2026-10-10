import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { getResults } from "./api/client";
import { ProvenanceBar } from "./components/Provenance";
import type { Provenance } from "./contracts.gen";
import { PROMISE } from "./format";
import { Results } from "./pages/ResultsPage";
import { issueFixture, resultsFixture } from "./test/fixtures";

function at(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

const REAL: Provenance = {
  contract_version: "1.0.0",
  data_label: "cached_real",
  snapshot_id: "abc123",
  data_as_of: "2026-10-01",
  config_hash: "0123456789ab",
  git_sha: "deadbee",
  availability_basis: "DATEA",
  generated_at: "2026-10-10T16:00:00Z",
};

describe("screens against the fixture API", () => {
  it("evidence links equal each complaint's nhtsa_url", async () => {
    at("/issue/g_6bc38243bb0a");
    const links = await screen.findAllByTestId("evidence-link");
    expect(links.map((a) => a.getAttribute("href"))).toEqual(issueFixture().evidence.items.map((c) => c.nhtsa_url));
  });

  it("vehicle page always renders the VIN lookup link and model-level wording", async () => {
    at("/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017");
    const vin = await screen.findByTestId("vin-link");
    expect(vin.getAttribute("href")).toBe("https://www.nhtsa.gov/recalls");
    expect(screen.getByText(/apply to this model and model year/)).toBeTruthy();
    expect(screen.getByText(/35 distinct complaints/)).toBeTruthy();
  });

  it("vehicle with no data shows the API's not-found message", async () => {
    at("/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=1999");
    expect(await screen.findByText("No complaints for this vehicle in the data range.")).toBeTruthy();
  });

  it("shows the synthetic banner, data label and data-as-of for fixture data", async () => {
    at("/");
    await waitFor(() => expect(screen.getAllByText(/SYNTHETIC TEST DATA/).length).toBeGreaterThan(0));
    expect(screen.getByTestId("header-meta").textContent).toContain("Synthetic test data");
    expect(screen.getByTestId("header-meta").textContent).toContain("Data as of");
  });

  it("held-out tab before export says it has not been run", async () => {
    at("/results?period=held_out");
    expect((await screen.findByTestId("held-out-not-run")).textContent).toBe(
      "Not yet run (thresholds frozen at freeze-v1)",
    );
  });
});

describe("hooks the Playwright smoke relies on (D-to-C e2e request)", () => {
  it("landing: promise verbatim, Make/Model/Year comboboxes, Show vehicle, hero replay link", async () => {
    at("/");
    expect((await screen.findByTestId("promise")).textContent).toBe(PROMISE);
    await screen.findByRole("combobox", { name: "Make" });
    for (const name of ["Make", "Model", "Year"]) {
      expect(screen.getByRole("combobox", { name })).toBeTruthy();
    }
    expect(screen.getByRole("button", { name: "Show vehicle" })).toBeTruthy();
    const hero = await screen.findByRole("link", { name: /Open replay/ });
    expect(hero.getAttribute("href")).toBe("/replay/E-0412");
  });

  it("replay: Restart, Step forward and Play buttons", async () => {
    at("/replay/E-0412");
    for (const name of ["Restart", "Step forward", "Play"]) {
      expect(await screen.findByRole("button", { name })).toBeTruthy();
    }
  });

  it("results: misses list visible without a click; real data shows config hash, git SHA and CSV link", () => {
    const data = { ...resultsFixture("development"), provenance: { ...REAL, data_label: "measured_evaluation" as const } };
    render(
      <MemoryRouter>
        <Results data={data} source="live" />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("misses-list")).toHaveProperty("open", true);
    const info = screen.getByTestId("run-info").textContent ?? "";
    expect(info).toContain("config hash 0123456789ab");
    expect(info).toContain("git SHA deadbee");
    expect(screen.getByTestId("results-csv").getAttribute("href")).toBe("/api/export/results.csv?period=development");
    expect(document.body.textContent).toMatch(/coverage/i);
    expect(document.body.textContent).toMatch(/chance/i);
  });
});

describe("synthetic banner logic", () => {
  it("no banner for real data; label and as-of date shown", () => {
    render(<ProvenanceBar provenance={REAL} source="live" />);
    expect(screen.queryByText(/SYNTHETIC TEST DATA/)).toBeNull();
    expect(screen.getByTestId("provenance").textContent).toContain("Real NHTSA records, precomputed");
    expect(screen.getByTestId("provenance").textContent).toContain("Data as of Oct 1, 2026");
  });

  it("banner whenever data_label is synthetic_fixture", () => {
    render(<ProvenanceBar provenance={{ ...REAL, data_label: "synthetic_fixture" }} />);
    expect(screen.getByRole("alert").textContent).toContain("SYNTHETIC TEST DATA");
  });

  it("offline source is labeled", () => {
    render(<ProvenanceBar provenance={REAL} source="offline" />);
    expect(screen.getByText("Offline demo data")).toBeTruthy();
  });
});

describe("live mode falls back to bundled /demo files when the API is unreachable", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("uses /demo/results_development.json when /api fails", async () => {
    vi.stubEnv("VITE_API_MODE", "live");
    const body = resultsFixture("development");
    const fetchMock = vi.fn(async (url: string) => {
      if (url.startsWith("/api/")) throw new TypeError("Failed to fetch");
      if (url === "/demo/results_development.json") {
        return new Response(JSON.stringify(body), { headers: { "content-type": "application/json" } });
      }
      return new Response("nope", { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const r = await getResults("development");
    expect(r.ok && r.source).toBe("offline");
    expect(fetchMock.mock.calls.map((c) => c[0])).toEqual([
      "/api/results?period=development",
      "/demo/results_development.json",
    ]);
  });

  it("returns the API's typed error when the API answers with one", async () => {
    vi.stubEnv("VITE_API_MODE", "live");
    const err = { error: { code: "not_found", message: "No such episode.", detail: null } };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(err), { status: 404, headers: { "content-type": "application/json" } })),
    );
    const r = await getResults("held_out");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toEqual(err);
  });
});
