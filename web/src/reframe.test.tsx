// Gate 1 reframe (EXECUTION_PLAN §2): the results page states the coverage-vs-chance result plainly,
// development results are PRELIMINARY until freeze-v1, and error states only offer a retry that can help.
// Expected strings are worked out by hand from the metric values below, not copied from format.ts.
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { ErrorState } from "./components/States";
import type { Metric } from "./contracts.gen";
import { coverageVerdict, periodNote } from "./format";
import { Results } from "./pages/ResultsPage";
import SelectorPage from "./pages/SelectorPage";
import { resultsFixture } from "./test/fixtures";

const metric = (name: Metric["name"], value: number, n: number, d: number, lo: number, hi: number): Metric => ({
  name, status: "measured", value, ci_low: lo, ci_high: hi, numerator: n, denominator: d, note: null,
});

describe("coverage verdict", () => {
  it("development fixture: 1/3 vs 1/10 meets the margin but the intervals overlap", () => {
    // 1/3 = 33.3%, 1/10 = 10.0%, gap 23.3 points >= 10; CIs 6.15-79.23% and 1.79-40.42% overlap
    const dev = resultsFixture("development");
    const get = (n: string) => dev.metrics.find((m) => m.name === n);
    expect(coverageVerdict(get("early_coverage_all"), get("chance_coverage"))).toBe(
      "Early-alert coverage was 33.3%; chance coverage was 10.0%. That is 23.3 percentage points above chance. " +
        "The margin set before the evaluation was 10 points above chance, and it is met, but the two 95% intervals " +
        "overlap, so the difference is uncertain.",
    );
  });

  it("a Gate-1-shaped result (23/257 vs 70/783) says plainly that nothing is shown", () => {
    // 23/257 = 0.089494, 70/783 = 0.089400: both 8.9%, gap 0.0094 points -> "the same as chance"
    const v = coverageVerdict(
      metric("early_coverage_all", 23 / 257, 23, 257, 0.06, 0.13),
      metric("chance_coverage", 70 / 783, 70, 783, 0.07, 0.11),
    );
    expect(v).toBe(
      "Early-alert coverage was 8.9%; chance coverage was 8.9%. That is the same as chance. The margin set before " +
        "the evaluation was 10 points above chance, so these results do not show that alerts came earlier for " +
        "investigated vehicles than for comparable vehicles that were never investigated.",
    );
  });

  it("below chance is called below, never above", () => {
    const v = coverageVerdict(
      metric("early_coverage_all", 0.05, 5, 100, 0.02, 0.11),
      metric("chance_coverage", 0.08, 8, 100, 0.04, 0.15),
    );
    expect(v).toContain("That is 3.0 percentage points below chance.");
    expect(v).toContain("do not show");
  });

  it("a gap of exactly 10 points meets the margin, as scripts/fill_numbers.py says", () => {
    // 30.0% - 20.0% = 10.0 points: not below the margin. In binary floats (0.3 - 0.2) * 100 is
    // 9.999999999999998, which must not turn the verdict around. CIs 20-41% and 15-25% overlap.
    const v = coverageVerdict(
      metric("early_coverage_all", 0.3, 30, 100, 0.2, 0.41),
      metric("chance_coverage", 0.2, 20, 100, 0.15, 0.25),
    );
    expect(v).toBe(
      "Early-alert coverage was 30.0%; chance coverage was 20.0%. That is 10.0 percentage points above chance. " +
        "The margin set before the evaluation was 10 points above chance, and it is met, but the two 95% intervals " +
        "overlap, so the difference is uncertain.",
    );
  });

  it("is absent while either metric is pending (held-out fixture)", () => {
    const ho = resultsFixture("held_out");
    const get = (n: string) => ho.metrics.find((m) => m.name === n);
    expect(coverageVerdict(get("early_coverage_all"), get("chance_coverage"))).toBeNull();
  });

  it("is rendered on the results page above the metrics", () => {
    render(
      <MemoryRouter>
        <Results data={resultsFixture("development")} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("coverage-verdict").textContent).toMatch(/^Early-alert coverage was 33\.3%/);
  });
});

describe("PRELIMINARY until freeze-v1", () => {
  it("development without a freeze tag is PRELIMINARY; with one it is not; held-out has no note", () => {
    expect(periodNote("development", null)).toMatch(/^PRELIMINARY: /);
    expect(periodNote("development", "freeze-v1")).not.toMatch(/PRELIMINARY/);
    expect(periodNote("held_out", "freeze-v1")).toBeNull();
  });

  it("the development fixture (freeze_tag null) shows the PRELIMINARY note", () => {
    render(
      <MemoryRouter>
        <Results data={resultsFixture("development")} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("period-note").textContent).toMatch(/^PRELIMINARY/);
  });
});

describe("error states", () => {
  it("no 'Try again' for a selection that does not exist (404) or is invalid (400)", () => {
    const retry = vi.fn();
    const { rerender } = render(<ErrorState error={{ error: { code: "not_found", message: "No complaints.", detail: null } }} retry={retry} />);
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    rerender(<ErrorState error={{ error: { code: "invalid_parameter", message: "Bad.", detail: null } }} retry={retry} />);
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
  });

  it("'Try again' when the service is down (503) or failed (500)", () => {
    const retry = vi.fn();
    const { rerender } = render(<ErrorState error={{ error: { code: "unavailable", message: "Down.", detail: null } }} retry={retry} />);
    screen.getByRole("button", { name: "Try again" }).click();
    expect(retry).toHaveBeenCalledTimes(1);
    rerender(<ErrorState error={{ error: { code: "internal", message: "Oops.", detail: null } }} retry={retry} />);
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
  });
});

describe("landing copy", () => {
  it("hero note never contains the banner text D's smoke counts (SYNTHETIC TEST DATA, any case)", async () => {
    render(
      <MemoryRouter>
        <SelectorPage />
      </MemoryRouter>,
    );
    const link = await screen.findByRole("link", { name: /Open replay/ });
    const card = link.closest("aside");
    expect(card).not.toBeNull();
    expect(card!.textContent).not.toMatch(/synthetic test data/i);
    expect(card!.textContent).toMatch(/made-up test records/);
  });

  it("states the reframed use and points to the comparison with chance", async () => {
    render(
      <MemoryRouter>
        <SelectorPage />
      </MemoryRouter>,
    );
    const p = await screen.findByTestId("reframe");
    expect(p.textContent).toMatch(/full complaint history/);
    expect(p.textContent).toMatch(/what was public before each\s+NHTSA investigation/);
    expect(p.querySelector("a")?.getAttribute("href")).toBe("/results");
  });
});
