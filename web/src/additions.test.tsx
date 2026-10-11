import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ProvenanceBar } from "./components/Provenance";
import type { Provenance } from "./contracts.gen";
import { earlyLeadPoints } from "./charts/data";
import { LeadTimeChart } from "./pages/ResultsPage";
import { episodeMarkers } from "./pages/VehiclePage";
import { resultsFixture, vehicleFixture } from "./test/fixtures";

const REAL: Provenance = {
  contract_version: "1.0.0",
  data_label: "cached_real",
  snapshot_id: "e808281f001a",
  data_as_of: "2026-10-01",
  config_hash: "0123456789ab",
  git_sha: "deadbee",
  availability_basis: "DATEA",
  generated_at: "2026-10-10T16:00:00Z",
};

describe("received-date experiment (PROJECT_SPEC §5, A3 decision LDATE_PLUS_7)", () => {
  it("is announced whenever availability_basis is LDATE_PLUS_7", () => {
    render(<ProvenanceBar provenance={{ ...REAL, availability_basis: "LDATE_PLUS_7" }} />);
    expect(screen.getByTestId("received-date-note").textContent).toMatch(/received-date experiment/i);
  });

  it("is absent for DATEA", () => {
    render(<ProvenanceBar provenance={REAL} />);
    expect(screen.queryByTestId("received-date-note")).toBeNull();
  });
});

describe("vehicle timeline episodes", () => {
  it("puts one ▲ on the first alert month of each episode", () => {
    // fixture: one STEERING episode, start_month 2018-04, alert_date 2018-05-01
    const m = episodeMarkers(vehicleFixture());
    expect(m.map((x) => [x.key, x.symbol, x.testId])).toEqual([["2018-04", "▲", "marker-alert"]]);
    expect(m[0].text).toBe("Alert: STEERING · May 1, 2018");
  });
});

describe("lead-time distribution (one point per matched early alert, no bins)", () => {
  it("maps exactly the fixture's early case: 167 days, family F-118, PE18-000", () => {
    expect(earlyLeadPoints(resultsFixture("development").cases)).toEqual([{ familyId: "F-118", actionNo: "PE18-000", leadDays: 167 }]);
  });

  it("shows the exact lead time in the summary and the data table", () => {
    render(
      <MemoryRouter>
        <LeadTimeChart cases={resultsFixture("development").cases} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("lead-time").textContent).toContain("One matched early alert: 167 days.");
    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    const rows = within(screen.getByTestId("lead-table")).getAllByTestId("lead-row");
    expect(rows.map((r) => [...r.querySelectorAll("th, td")].map((c) => c.textContent))).toEqual([["F-118", "PE18-000", "167"]]);
  });

  it("says so when no case has a lead time (held-out before the run), without a chart", () => {
    render(<LeadTimeChart cases={resultsFixture("held_out").cases} />);
    expect(screen.getByText("No matched early alerts with a lead time in this results file yet.")).toBeTruthy();
    expect(screen.queryByRole("slider")).toBeNull();
  });
});
