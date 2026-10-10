import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { Replay } from "../contracts.gen";
import { replayFixture } from "../test/fixtures";
import { ReplayView } from "./ReplayPage";

function renderReplay(data: Replay) {
  return render(
    <MemoryRouter>
      <ReplayView data={data} />
    </MemoryRouter>,
  );
}

const barMonths = () => screen.queryAllByTestId("bar").map((b) => b.getAttribute("data-month"));
const forward = () => fireEvent.click(screen.getByRole("button", { name: "Step forward" }));

describe("replay", () => {
  it("never draws a bar for a month after the current frame's cutoff", () => {
    const data = replayFixture();
    renderReplay(data);
    data.frames.forEach((frame, i) => {
      const months = barMonths();
      // bars are exactly the frames up to and including this one
      expect(months).toEqual(data.frames.slice(0, i + 1).map((f) => f.month));
      // and every drawn month ends before this frame's exclusive cutoff
      for (const m of months) expect(`${m}-01` < frame.cutoff).toBe(true);
      if (i < data.frames.length - 1) forward();
    });
  });

  it("shows the alert marker only from the frame whose cutoff >= alert_date", () => {
    // fixture alert_date 2018-05-01; frame 2018-04 has cutoff 2018-05-01 (first with cutoff >= it)
    const data = replayFixture();
    renderReplay(data);
    const seen: Record<string, boolean> = {};
    data.frames.forEach((f, i) => {
      seen[f.month] = screen.queryAllByTestId("marker-alert").length > 0;
      if (i < data.frames.length - 1) forward();
    });
    expect(Object.entries(seen).filter(([, v]) => v)[0][0]).toBe("2018-04");
    expect(seen["2018-03"]).toBe(false);
    expect(seen["2018-12"]).toBe(true);
  });

  it("reveals the investigation (◆, labeled later reveal) only once its date has passed", () => {
    // investigation opened 2018-10-15 -> first frame with cutoff >= that is 2018-10 (cutoff 2018-11-01)
    const data = replayFixture();
    renderReplay(data);
    const firstOutcome = data.frames.findIndex((_, i) => {
      if (i > 0) forward();
      return screen.queryAllByTestId("marker-investigation").length > 0;
    });
    expect(data.frames[firstOutcome].month).toBe("2018-10");
    const legend = screen.getAllByTestId("legend-marker").map((l) => l.textContent);
    expect(legend.some((t) => t?.includes("◆") && t.includes("Investigation opened") && t.includes("(later reveal)"))).toBe(
      true,
    );
    // the recall (2019-02-04) is after the last cutoff (2019-01-01): never drawn on the timeline
    expect(legend.some((t) => t?.includes("Recall"))).toBe(false);
    expect(screen.queryAllByTestId("marker-recall")).toHaveLength(0);
    // the marker element itself carries the symbol and the "later reveal" label (D's smoke hook)
    const inv = screen.getByTestId("marker-investigation").textContent ?? "";
    expect(inv).toContain("◆");
    expect(inv).toContain("later reveal");
    expect(screen.getByTestId("marker-alert").textContent).toContain("▲");
  });

  it("is keyboard operable and shows the documented outcome at the end", () => {
    const data = replayFixture();
    renderReplay(data);
    const controls = screen.getByRole("group", { name: "Replay controls" });
    fireEvent.keyDown(controls, { key: "ArrowRight" });
    expect(barMonths()).toHaveLength(2);
    fireEvent.keyDown(controls, { key: "End" });
    expect(barMonths()).toHaveLength(data.frames.length);
    expect(screen.getByTestId("outcome-status").textContent).toBe(
      "Alert dated 60 to 730 days before the investigation opened",
    );
    expect(screen.getByTestId("vin-link").getAttribute("href")).toBe("https://www.nhtsa.gov/recalls");
    fireEvent.keyDown(controls, { key: "Home" });
    expect(barMonths()).toHaveLength(1);
    expect(screen.queryByTestId("outcome-status")).toBeNull();
  });

  it("greys a partial month and labels it 'partial'", () => {
    const data = replayFixture();
    const last = data.frames.length - 1;
    data.frames[last] = { ...data.frames[last], partial: true, score: null, baseline_lambda: null };
    renderReplay(data);
    fireEvent.keyDown(screen.getByRole("group", { name: "Replay controls" }), { key: "End" });
    const bar = screen.getAllByTestId("bar").find((b) => b.getAttribute("data-month") === data.frames[last].month)!;
    expect(bar.getAttribute("data-tone")).toBe("partial");
    expect(screen.getAllByText("partial").length).toBeGreaterThan(0);
    expect(screen.getByTestId("frame-status").textContent).toContain("(partial month)");
  });
});
