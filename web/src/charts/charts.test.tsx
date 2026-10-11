// Owner: C. Focused tests for the Bklit charts and their data mappings. Expected values are read off the
// contract fixtures by hand (contracts/fixtures/api) or computed independently in the test, never copied
// from the implementation.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MotionConfig } from "motion/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getResults } from "../api/client";
import type { EvalCase, Metric, Replay, ReplayMarker, VehicleResponse } from "../contracts.gen";
import { CoverageSection } from "../pages/ResultsPage";
import { ReplayView } from "../pages/ReplayPage";
import { frameMarkers, framePoints } from "../replay";
import { resultsFixture, replayFixture, vehicleFixture } from "../test/fixtures";
import { testMedia } from "../test/setup";
import { ChartFrame } from "./ChartFrame";
import ComplaintTimeline from "./ComplaintTimeline";
import { coverageRow, earlyLeadPoints, fractionText, metricFraction, timelineRows, topIssueGroups } from "./data";

vi.mock("../api/client", async (orig) => {
  const m = await orig<typeof import("../api/client")>();
  return { ...m, getResults: vi.fn(m.getResults) };
});

afterEach(() => {
  testMedia.reducedMotion = false;
  testMedia.compact = false;
  vi.mocked(getResults).mockReset();
});

const metric = (name: Metric["name"], numerator: number | null, denominator: number | null, status: Metric["status"] = "measured"): Metric => ({
  name, status, value: numerator !== null && denominator ? numerator / denominator : null, numerator, denominator, ci_low: null, ci_high: null, note: null,
});

describe("data mappings (API value -> chart value)", () => {
  it("complaint timeline rows: one stacked series per tone, the API count in exactly one of them", () => {
    const data = replayFixture();
    const last = data.frames.length - 1;
    const rows = timelineRows(framePoints(data.frames, last));
    data.frames.forEach((f, i) => {
      const r = rows[i];
      expect(r.key).toBe(f.month);
      expect(r.value).toBe(f.n_distinct);
      const nonNull = [r.normal, r.alert, r.partial].filter((v) => v !== null);
      expect(nonNull).toEqual([f.n_distinct]);
      expect(r.alert !== null).toBe(!f.partial && f.alert_active);
    });
  });

  it("months after the replay cutoff carry no value in any series (nothing can be drawn early)", () => {
    const data = replayFixture();
    const rows = timelineRows(framePoints(data.frames, 2));
    for (const r of rows.slice(3)) expect([r.value, r.normal, r.alert, r.partial]).toEqual([null, null, null, null]);
    for (const r of rows.slice(3)) expect(r.detail).toEqual([]);
  });

  it("issue distribution: top five by count, highest first, API order kept for ties", () => {
    const v = vehicleFixture();
    const base = v.components[0];
    const make = (system: string, n: number) => ({ ...base, group: { ...base.group, group_id: `g_${system}`, comp_system: system, distinct_complaints: n } });
    const data: VehicleResponse = { ...v, components: [make("A", 3), make("B", 9), make("C", 3), make("D", 12), make("E", 3), make("F", 1), make("G", 9)] };
    expect(topIssueGroups(data).map((r) => [r.name, r.complaints])).toEqual([
      ["D", 12],
      ["B", 9],
      ["G", 9],
      ["A", 3],
      ["C", 3],
    ]);
  });

  it("issue distribution on the fixture: its two groups with their exact counts", () => {
    // vehicle.json: STEERING 30, SERVICE BRAKES 7
    expect(topIssueGroups(vehicleFixture()).map((r) => [r.name, r.complaints])).toEqual([
      ["STEERING", 30],
      ["SERVICE BRAKES", 7],
    ]);
  });

  it("coverage: fraction and percentage from the metric's own numerator and denominator only", () => {
    const f = metricFraction(metric("early_coverage_all", 23, 257))!;
    expect(f.numerator).toBe(23);
    expect(f.denominator).toBe(257);
    expect(f.percent).toBeCloseTo((23 / 257) * 100, 10);
    expect(fractionText(f)).toBe("23 of 257 (8.9%)");
  });

  it("coverage: no fraction (so no bar) when pending, not applicable, or a count is missing", () => {
    expect(metricFraction(metric("early_coverage_all", null, null, "pending"))).toBeNull();
    expect(metricFraction(metric("early_coverage_all", 3, null))).toBeNull();
    expect(metricFraction(metric("early_coverage_all", null, 10))).toBeNull();
    expect(metricFraction(metric("early_coverage_all", 0, 0))).toBeNull();
    expect(metricFraction(undefined)).toBeNull();
  });

  it("development and held-out stay separate rows, each from its own file", () => {
    const dev = coverageRow("development", "Development period", resultsFixture("development").metrics);
    const held = coverageRow("held_out", "Held-out period", resultsFixture("held_out").metrics);
    const devCov = resultsFixture("development").metrics.find((m) => m.name === "early_coverage_all")!;
    expect(dev.recallRadarFraction?.numerator).toBe(devCov.numerator);
    expect(dev.recallRadarFraction?.denominator).toBe(devCov.denominator);
    // the held-out fixture is pending: no values at all, nothing borrowed from development
    expect([held.recallRadar, held.chance, held.recallRadarFraction, held.chanceFraction]).toEqual([null, null, null, null]);
  });

  it("lead times: malformed or non-early cases are skipped, values never altered", () => {
    const c = resultsFixture("development").cases[0];
    const cases: EvalCase[] = [
      { ...c, family_id: "F-1", status: "early", lead_days: 60 },
      { ...c, family_id: "F-2", status: "early", lead_days: null },
      { ...c, family_id: "F-3", status: "late", lead_days: 12 },
      { ...c, family_id: "F-4", status: "early", lead_days: 730 },
    ];
    expect(earlyLeadPoints(cases).map((p) => [p.familyId, p.leadDays])).toEqual([
      ["F-1", 60],
      ["F-4", 730],
    ]);
  });
});

const recall = (date: string, campno: string, link?: "issue" | "vehicle"): ReplayMarker => ({
  type: "recall_reported", date, label: `Recall campaign ${campno} reported`, is_outcome: true, action_no: null, match_tier: null, lead_days: null, campno, ...(link ? { link } : {}),
});

describe("replay markers", () => {
  it("issue-linked and vehicle-level recalls are different kinds, drawn differently", async () => {
    const r: Replay = replayFixture();
    r.markers = [...r.markers, recall("2018-02-01", "19V111000", "vehicle"), recall("2018-06-10", "18V000000", "issue")];
    const m = frameMarkers(r.frames, r.markers, r.frames.length - 1, { onRecall: () => {} });
    expect(m.find((x) => x.campno === "18V000000")).toMatchObject({ kind: "recall-issue", link: "issue", glyph: "│", identifier: "18V000000" });
    expect(m.find((x) => x.campno === "19V111000")).toMatchObject({ kind: "recall-vehicle", link: "vehicle" });
    render(
      <MemoryRouter>
        <ReplayView data={r} />
      </MemoryRouter>,
    );
    fireEvent.keyDown(screen.getByRole("group", { name: "Replay controls" }), { key: "End" });
    const buttons = await screen.findAllByTestId("marker-recall");
    const kinds = Object.fromEntries(buttons.map((b) => [b.getAttribute("aria-label")!.match(/\d\dV\d{6}/)![0], b.getAttribute("data-kind")]));
    expect(kinds).toEqual({ "18V000000": "recall-issue", "19V111000": "recall-vehicle" });
    expect(buttons.every((b) => b.className.includes(`rr-marker-${b.getAttribute("data-kind")}`))).toBe(true);
  });

  it("a recall marker without a link field is not claimed as issue-linked", () => {
    const r = replayFixture();
    r.markers = [...r.markers, recall("2018-02-01", "17V000001")];
    const m = frameMarkers(r.frames, r.markers, r.frames.length - 1);
    expect(m.find((x) => x.text.includes("17V000001"))).toMatchObject({ kind: "recall", link: null });
  });

  it("keyboard focus on a marker shows its tooltip (type, identifier, date basis, link); Esc hides it", async () => {
    const r = replayFixture();
    render(
      <MemoryRouter>
        <ReplayView data={r} />
      </MemoryRouter>,
    );
    fireEvent.keyDown(screen.getByRole("group", { name: "Replay controls" }), { key: "End" });
    const inv = await screen.findByTestId("marker-investigation");
    act(() => inv.focus());
    const tip = screen.getByRole("tooltip");
    expect(inv.getAttribute("aria-describedby")).toBe(tip.id);
    expect(tip.textContent).toContain("Investigation opened");
    expect(tip.textContent).toContain("Identifier: PE18-000");
    expect(tip.textContent).toContain("Oct 15, 2018: Date NHTSA opened the investigation (later reveal)");
    fireEvent.keyDown(inv, { key: "Escape" });
    expect(screen.queryByRole("tooltip")).toBeNull();
  });
});

describe("keyboard data exploration", () => {
  it("the timeline explorer reads each drawn month and shows Bklit's tooltip on focus", async () => {
    const r = replayFixture();
    render(
      <MemoryRouter>
        <ReplayView data={r} />
      </MemoryRouter>,
    );
    fireEvent.keyDown(screen.getByRole("group", { name: "Replay controls" }), { key: "End" });
    const slider = await screen.findByRole("slider", { name: /Distinct complaints per month/ });
    act(() => slider.focus());
    const lastFrame = r.frames[r.frames.length - 1];
    expect(slider.getAttribute("aria-valuemax")).toBe(String(r.frames.length));
    expect(slider.getAttribute("aria-valuetext")).toContain(`${lastFrame.n_distinct} distinct complaint`);
    fireEvent.keyDown(slider, { key: "Home" });
    const first = r.frames[0];
    expect(slider.getAttribute("aria-valuenow")).toBe("1");
    expect(slider.getAttribute("aria-valuetext")).toMatch(new RegExp(`^Nov 2017: ${first.n_distinct} distinct complaint`));
    // Bklit's own tooltip box is showing the same month
    await waitFor(() => expect(document.body.textContent).toContain("Nov 2017"));
  });
});

describe("states", () => {
  it("empty: says nothing matches in the cached dataset, renders no chart and no zero bars", () => {
    render(
      <ChartFrame title="Test chart" description="d" state={{ kind: "empty", message: "No matching records in the cached dataset." }}>
        <p data-testid="chart-body" />
      </ChartFrame>,
    );
    expect(screen.getByText("No matching records in the cached dataset.")).toBeTruthy();
    expect(screen.queryByTestId("chart-body")).toBeNull();
    expect(screen.queryAllByTestId("bar")).toHaveLength(0);
  });

  it("loading: a reserved, labelled skeleton with no values", () => {
    render(
      <ChartFrame title="Test chart" description="d" state={{ kind: "loading" }}>
        <p data-testid="chart-body" />
      </ChartFrame>,
    );
    const sk = screen.getByRole("status");
    expect(sk.className).toContain("rr-chart-skeleton");
    expect(sk.textContent).toBe("Loading Test chart…");
  });

  it("API error on the coverage chart: message + retry, no zero bars; held-out failure is text", async () => {
    vi.mocked(getResults).mockImplementation(async (p) =>
      p === "development" ? { ok: false, status: 503, error: { error: { code: "unavailable", message: "Service unavailable", detail: null } } } : { ok: true, data: resultsFixture("held_out"), source: "fixture" },
    );
    render(
      <MemoryRouter>
        <CoverageSection />
      </MemoryRouter>,
    );
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Development results could not be loaded: Service unavailable");
    expect(within(alert).getByRole("button", { name: "Try again" })).toBeTruthy();
    expect(screen.queryByText(/0 of /)).toBeNull();
  });

  it("coverage chart: both periods, fraction + percentage labels; pending held-out says why", async () => {
    vi.mocked(getResults).mockImplementation(async (p) => ({ ok: true, data: resultsFixture(p), source: "fixture" }));
    render(
      <MemoryRouter>
        <CoverageSection />
      </MemoryRouter>,
    );
    const chart = await screen.findByTestId("coverage-chart");
    const dev = resultsFixture("development").metrics;
    const cov = dev.find((m) => m.name === "early_coverage_all")!;
    const ch = dev.find((m) => m.name === "chance_coverage")!;
    const want = (m: Metric) => `${m.numerator} of ${m.denominator} (${((m.numerator! / m.denominator!) * 100).toFixed(1)}%)`;
    await waitFor(() => expect(chart.textContent).toContain(`Development period: early-alert coverage ${want(cov)}, chance coverage ${want(ch)}.`));
    expect(chart.textContent).toContain("Held-out period: Not yet run");
    fireEvent.click(within(chart).getByRole("button", { name: "Table" }));
    expect(within(screen.getByTestId("coverage-row-development")).getAllByRole("cell").map((c) => c.textContent)).toEqual([want(cov), want(ch)]);
    expect(chart.textContent).not.toMatch(/outperform/i);
  });
});

describe("motion", () => {
  it("reduced motion: sections fade without moving (no transform)", () => {
    // The app uses reducedMotion="user", which follows the OS setting through motion's own media listener
    // (read once per page, so it cannot be toggled between tests); "always" runs the same reduced path.
    render(
      <MotionConfig reducedMotion="always">
        <ChartFrame title="Test chart" description="d" state={{ kind: "empty", message: "Nothing." }}>
          <p />
        </ChartFrame>
      </MotionConfig>,
    );
    // no offset at any moment, including the first frame before the fade starts
    const fig = screen.getByRole("figure");
    expect(fig.style.transform === "" || fig.style.transform === "none").toBe(true);
  });

  it("remounting a chart does not duplicate its explorer, markers or tooltips", async () => {
    const r = replayFixture();
    const points = framePoints(r.frames, r.frames.length - 1);
    const markers = frameMarkers(r.frames, r.markers, r.frames.length - 1);
    const view = () => (
      <ChartFrame title="Remount" description="d" state={{ kind: "ready" }}>
        <ComplaintTimeline title="Remount" points={points} markers={markers} />
      </ChartFrame>
    );
    const { unmount } = render(view());
    await screen.findAllByTestId("bar");
    unmount();
    render(view());
    await screen.findAllByTestId("bar");
    expect(document.querySelectorAll(".rr-explorer")).toHaveLength(1);
    expect(document.querySelectorAll(".rr-marker-layer")).toHaveLength(1);
    expect(screen.getAllByTestId("marker-alert")).toHaveLength(1);
  });
});
