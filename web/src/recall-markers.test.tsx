// PRD v2 F3 (C side): recall markers hidden until the cutoff is past their date (unless "Show later outcomes"),
// distinct labels for issue / vehicle links, keyboard buttons opening the F1 card, Esc returns focus,
// a missing campaign says "Record unavailable", and replays without linked recalls are unchanged.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { Replay, ReplayMarker } from "./contracts.gen";
import { ReplayView } from "./pages/ReplayPage";
import { frameMarkers } from "./replay";
import { replayFixture } from "./test/fixtures";

const recall = (date: string, campno: string, link: "issue" | "vehicle"): ReplayMarker => ({
  type: "recall_reported", date, label: `Recall campaign ${campno} reported`, is_outcome: true,
  action_no: null, match_tier: null, lead_days: null, campno, link,
});
function withRecalls(): Replay {
  const r = replayFixture();
  r.markers = [...r.markers, recall("2018-02-01", "99V999000", "vehicle"), recall("2018-03-05", "19V111000", "vehicle"),
    recall("2018-06-10", "18V000000", "issue")].sort((a, b) => a.date.localeCompare(b.date));
  return r;
}
const show = (r: Replay) => render(<MemoryRouter><ReplayView data={r} /></MemoryRouter>);
const recallButtons = () => screen.queryAllByTestId("recall-marker-button");

describe("recall marker visibility", () => {
  it("hidden until the frame cutoff is past the date; toggle shows later outcomes", () => {
    const r = withRecalls();
    const at = (i: number, showLater = false) =>
      frameMarkers(r.frames, r.markers, i, { showLater, onRecall: () => {} }).filter((m) => m.campno).map((m) => m.campno);
    expect(at(0)).toEqual([]); // cutoff 2017-12-01
    expect(at(3)).toEqual(["99V999000"]); // cutoff 2018-03-01 > 2018-02-01; 2018-03-05 not yet
    expect(at(4)).toEqual(["99V999000", "19V111000"]); // cutoff 2018-04-01
    expect(at(7)).toEqual(["99V999000", "19V111000", "18V000000"]); // cutoff 2018-07-01
    expect(at(0, true)).toEqual(["99V999000", "19V111000", "18V000000"]);
  });

  it("issue and vehicle links read differently", () => {
    show(withRecalls());
    fireEvent.click(screen.getByLabelText(/Show later outcomes/));
    const texts = recallButtons().map((b) => b.textContent);
    expect(texts.some((t) => t!.startsWith("Recall linked to this issue: campaign 18V000000"))).toBe(true);
    expect(texts.some((t) => t!.startsWith("Other recall for this model: campaign 19V111000"))).toBe(true);
  });
});

describe("recall drawer", () => {
  it("opens the right campaign card; Esc closes and returns focus to the marker", async () => {
    show(withRecalls());
    fireEvent.click(screen.getByLabelText(/Show later outcomes/));
    const btn = recallButtons().find((b) => b.textContent!.includes("18V000000"))!;
    btn.focus();
    fireEvent.click(btn);
    const drawer = await screen.findByTestId("recall-drawer");
    const card = await within(drawer).findByTestId("recall-card");
    expect(card.textContent).toContain("NHTSA campaign 18V000000");
    expect(document.activeElement?.textContent).toBe("Close");
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByTestId("recall-drawer")).toBeNull();
    await new Promise((r) => setTimeout(r, 5));
    expect(document.activeElement).toBe(btn);
  });

  it("SVG markers are keyboard buttons (Enter)", async () => {
    show(withRecalls());
    fireEvent.click(screen.getByLabelText(/Show later outcomes/));
    const svgMarker = screen.getAllByRole("button").find((b) => b.tagName.toLowerCase() === "text" && /19V111000/.test(b.getAttribute("aria-label") ?? ""))!;
    fireEvent.keyDown(svgMarker, { key: "Enter" });
    expect(await within(await screen.findByTestId("recall-drawer")).findByTestId("recall-card")).toBeTruthy();
  });

  it("a campaign missing from the data says Record unavailable, without crashing", async () => {
    show(withRecalls());
    fireEvent.click(screen.getByLabelText(/Show later outcomes/));
    fireEvent.click(recallButtons().find((b) => b.textContent!.includes("99V999000"))!);
    expect((await screen.findByTestId("recall-unavailable")).textContent).toMatch(/^Record unavailable/);
  });
});

describe("replays without linked recalls", () => {
  it("have no toggle and no recall buttons", () => {
    show(replayFixture());
    expect(screen.queryByLabelText(/Show later outcomes/)).toBeNull();
    expect(recallButtons()).toHaveLength(0);
  });
});
