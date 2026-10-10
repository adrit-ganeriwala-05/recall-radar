import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { EvaluationSummary } from "../contracts.gen";
import { fmtNumber, METRICS, roundDecimal } from "../format";
import { allResultsFiles, resultsFixture } from "../test/fixtures";
import { Results } from "./ResultsPage";

function renderResults(data: EvaluationSummary) {
  return render(
    <MemoryRouter>
      <Results data={data} />
    </MemoryRouter>,
  );
}

const card = (name: string) => screen.getByTestId(`metric-${name}`);
const value = (name: string) => within(card(name)).getByTestId("metric-value").textContent;

describe("results page, development fixture (expected strings hand-derived from the JSON)", () => {
  it("shows exactly the fixture's numbers, CI bounds and fractions", () => {
    renderResults(resultsFixture("development"));
    // value 3 / 1 -> counts
    expect(value("eligible_families")).toBe("3");
    expect(value("excluded_families")).toBe("1");
    // 1/3 = 33.33..% ; CI 0.0615 -> 6.15% -> 6.2% ; 0.7923 -> 79.23% -> 79.2%
    expect(value("early_coverage_all")).toBe("33.3%");
    expect(card("early_coverage_all").textContent).toContain("1 of 3");
    expect(card("early_coverage_all").textContent).toContain("CI 6.2% to 79.2%");
    // 0.1 -> 10.0% ; CI 0.0179 -> 1.8% ; 0.4042 -> 40.4%
    expect(value("chance_coverage")).toBe("10.0%");
    expect(card("chance_coverage").textContent).toContain("1 of 10");
    expect(card("chance_coverage").textContent).toContain("CI 1.8% to 40.4%");
    expect(value("median_lead_days")).toBe("167 days");
    expect(value("lead_days_q1")).toBe("167 days");
    expect(value("lead_days_q3")).toBe("167 days");
    expect(value("episodes_per_month")).toBe("0.50");
  });

  it("rounds shares half-up from the JSON's decimal value (0.0115 -> 1.2%, 0.0045 -> 0.5%)", () => {
    const data = resultsFixture("development");
    data.metrics = data.metrics.map((m) =>
      m.name === "chance_coverage" ? { ...m, value: 0.0115, ci_low: 0.0045, ci_high: 0.0955 } : m,
    );
    renderResults(data);
    expect(value("chance_coverage")).toBe("1.2%");
    expect(card("chance_coverage").textContent).toContain("CI 0.5% to 9.6%");
  });

  it("renders pending as 'Not yet measured' and not_applicable as a dash, never a number", () => {
    renderResults(resultsFixture("development"));
    for (const n of ["early_coverage_sample", "ingestion_retained_share", "pipeline_runtime_s"]) {
      expect(value(n)).toBe("Not yet measured");
    }
    for (const n of ["top25_matched", "top25_unmatched", "top25_ambiguous"]) {
      expect(value(n)).toBe("—");
    }
  });

  it("lists misses, unmatched and ambiguous expanded by default", () => {
    renderResults(resultsFixture("development"));
    for (const g of ["misses-list", "group-unmatched", "group-ambiguous"]) {
      expect(screen.getByTestId(g)).toHaveProperty("open", true);
    }
    expect(screen.getByTestId("group-matched")).toHaveProperty("open", false);
    // two misses in the fixture: PE18-001 and DP19-000
    const missed = within(screen.getByTestId("misses-list")).getAllByTestId("case-row");
    expect(missed.map((r) => r.querySelector("th")?.textContent?.split(" ")[0])).toEqual(["PE18-001", "DP19-000"]);
  });
});

describe("results page, held-out before the frozen run", () => {
  it("shows the not-yet-run notice and no metric numbers at all", () => {
    renderResults(resultsFixture("held_out"));
    expect(screen.getByTestId("held-out-not-run").textContent).toBe("Not yet run (thresholds frozen at freeze-v1)");
    for (const el of screen.getAllByTestId("metric-value")) {
      expect(el.textContent).toBe("Not yet measured");
      expect(el.textContent).not.toMatch(/\d/);
    }
    expect(document.querySelectorAll(".metric-detail")).toHaveLength(0);
  });
});

describe("agreement: rendered results equal every results JSON we ship (fixtures + exports/demo)", () => {
  it.each(allResultsFiles())("%s", (_file, data) => {
    renderResults(data);
    expect(screen.getAllByTestId(/^metric-(?!value)/)).toHaveLength(data.metrics.length);
    for (const m of data.metrics) {
      const kind = METRICS[m.name].kind;
      const text = card(m.name).textContent ?? "";
      if (m.status === "pending") expect(value(m.name)).toBe("Not yet measured");
      if (m.status === "not_applicable") expect(value(m.name)).toBe("—");
      if (m.status === "measured") {
        expect(value(m.name)).toBe(fmtNumber(kind, m.value!));
        if (m.ci_low !== null && m.ci_high !== null) {
          expect(text).toContain(fmtNumber(kind, m.ci_low));
          expect(text).toContain(fmtNumber(kind, m.ci_high));
        }
        if (m.numerator !== null && m.denominator !== null) expect(text).toContain(`${m.numerator} of ${m.denominator}`);
      }
    }
  });
});

describe("roundDecimal", () => {
  it.each([
    [0.0115 * 100, 1, "1.2"], // binary 1.1499999999999999
    [1.45, 1, "1.5"], // (1.45).toFixed(1) === "1.4"
    [79.23, 1, "79.2"],
    [0.5, 2, "0.50"],
    [167, 0, "167"],
    [2.5, 0, "3"],
    [0.04, 1, "0.0"],
  ])("roundDecimal(%s, %s) = %s", (x, d, want) => {
    expect(roundDecimal(x, d)).toBe(want);
  });
});
