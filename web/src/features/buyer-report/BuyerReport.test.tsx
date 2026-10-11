// Owner: D. F8 content rules (PRD_v2 §4 F8.3–F8.5). The one-page PDF check is web/e2e/buyer-report.spec.ts.
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import base from "../../../../contracts/fixtures/api/report.json";
import type { ReportData } from "../../contracts.gen";
import { BuyerReport, REPORT_TITLE } from "./BuyerReport";

const data = base as unknown as ReportData;
const GEN = new Date("2026-10-11T12:00:00Z");

function view(d: ReportData = data) {
  return render(<BuyerReport data={d} generated={GEN} />);
}

describe("BuyerReport", () => {
  it("shows the title, vehicle, dates, counting basis and generation date", () => {
    view();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(REPORT_TITLE);
    expect(REPORT_TITLE).toBe("Used-car complaint and recall summary");
    expect(screen.getByText("2017 EXAMPLE MOTORS ROADSTER")).toBeTruthy();
    expect(screen.getByText("Jan 4, 2016 – Jun 28, 2019")).toBeTruthy(); // fixture range, by hand
    expect(screen.getByText("Oct 11, 2026")).toBeTruthy();
    expect(screen.getByText("35 complaints")).toBeTruthy();
    expect(screen.getByText("(distinct NHTSA complaint IDs)")).toBeTruthy();
  });

  it("lists exactly what the API selected, with 'showing n of m' for each list", () => {
    const { container } = view();
    expect(container.textContent).toContain("Showing 2 of 2 component groups.");
    expect(container.textContent).toContain("Showing 1 of 1 investigations.");
    expect(container.textContent).toContain("Showing 3 of 3 recall campaigns.");
    for (const c of data.campaigns) expect(screen.getByRole("link", { name: c.campno })).toBeTruthy();
    expect(container.textContent).toContain(`Selection: ${data.selection_rule}`);
  });

  it("links to the full vehicle page only when a list is cut, and always to the NHTSA VIN lookup", () => {
    const cut = { ...data, total_groups: 9, total_campaigns: 20 };
    view(cut);
    expect(screen.getAllByRole("link", { name: "See all on the vehicle page" })).toHaveLength(2);
    const vin = screen.getAllByRole("link", { name: "https://www.nhtsa.gov/recalls" });
    expect(vin[0].getAttribute("href")).toBe("https://www.nhtsa.gov/recalls");
  });

  it("shows the first line of the official remedy verbatim, labelled, and nothing else of the recall text", () => {
    const { container } = view();
    const c = data.campaigns[0]!;
    const first = (c.remedy ?? "").split("\n")[0];
    expect(container.textContent).toContain(`Remedy (official NHTSA text): ${first}`);
    expect(container.textContent).not.toContain("Owner letters are expected"); // second line of the remedy
    expect(container.textContent).not.toContain(c.consequence ?? "@@");
  });

  it("handles a vehicle with no data", () => {
    const empty: ReportData = {
      ...data,
      top_groups: [], shown_n: 0, total_groups: 0, investigations: [], total_investigations: 0,
      campaigns: [], total_campaigns: 0, distinct_complaints: 0, complaint_date_range: { start: null, end: null },
    };
    view(empty);
    expect(screen.getByText("No complaints for this vehicle in this dataset.")).toBeTruthy();
    expect(screen.getByText(/No matching recalls in this cached dataset/)).toBeTruthy();
    expect(screen.getByText("not stated – not stated")).toBeTruthy();
  });

  it("contains no VIN field, draft text, score, 'safe' or comparative wording, and no 'Download PDF'", () => {
    const { container } = view();
    const t = (container.textContent ?? "").toLowerCase();
    for (const bad of [/\bsafe\b/, /\bscore\b/, /failure rate/, /safer|more reliable|less reliable/, /download pdf/, /what happened, in my words/]) {
      expect(t).not.toMatch(bad);
    }
    expect(within(container).queryByLabelText(/vin/i)).toBeNull();
  });
});
