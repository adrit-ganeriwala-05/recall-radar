// PRD v2 F1 (C side): banners only on === true, AI label only on accepted, official text verbatim and always
// visible, one card per campno, VIN link on every card, forbidden phrases never rendered.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AI_LABEL, NO_RECALLS_TEXT, RecallCard, RecallCards } from "./components/RecallCard";
import type { RecallCampaign, VehicleKey } from "./contracts.gen";
import VehiclePage from "./pages/VehiclePage";

const V: VehicleKey = { make: "EXAMPLE MOTORS", model: "ROADSTER", model_year: 2017 };
const card = (o: Partial<RecallCampaign>): RecallCampaign => ({
  campno: "18V000000", component: "STEERING", report_date: "2019-02-04", summary: "Bolt may loosen.",
  consequence: null, remedy: null, park_it: null, park_outside: null, report_date_basis: "Report received date (RCDATE)",
  source_url: "https://www.nhtsa.gov/recalls", snapshot_id: "e808281f001a", explanation: null, ...o,
});
const one = (c: RecallCampaign) => render(<RecallCard campaign={c} vehicle={V} dataAsOf="2026-10-10" />);

describe("recall card banners", () => {
  it.each([
    [true, false, ["Do not drive — NHTSA campaign 18V000000"]],
    [false, true, ["Park outside — NHTSA campaign 18V000000"]],
    [true, true, ["Do not drive — NHTSA campaign 18V000000", "Park outside — NHTSA campaign 18V000000"]],
    [false, false, []],
    [null, null, []],
  ])("park_it=%s park_outside=%s", (a, b, want) => {
    one(card({ park_it: a as boolean | null, park_outside: b as boolean | null }));
    expect(screen.queryAllByRole("alert").map((e) => e.textContent)).toEqual(want);
  });

  it('a "false" string that slips past the type never shows a banner', () => {
    one(card({ park_it: "false" as unknown as boolean, park_outside: "yes" as unknown as boolean }));
    expect(screen.queryAllByRole("alert")).toHaveLength(0);
  });
});

describe("recall card content", () => {
  it("official text is shown verbatim as text, markup-like characters included", () => {
    const { container } = one(card({ summary: "Bolt <b>may</b> loosen & fall.\nSecond line." }));
    expect(screen.getByText("Official NHTSA text")).toBeTruthy();
    const dd = container.querySelector(".official-text")!;
    expect(dd.textContent).toBe("Bolt <b>may</b> loosen & fall.\nSecond line.");
    expect(dd.querySelector("b")).toBeNull();
  });

  it("missing fields are omitted; date carries its basis; VIN link on the card", () => {
    one(card({ consequence: null, remedy: "Dealers will fix it." }));
    expect(screen.queryByText("Consequence")).toBeNull();
    expect(screen.getByText("Remedy")).toBeTruthy();
    expect(screen.getByText(/Reported Feb 4, 2019 \(Report received date \(RCDATE\)\)/)).toBeTruthy();
    const vin = screen.getByTestId("recall-vin");
    expect(vin.textContent).toMatch(/^This campaign covers the 2017 EXAMPLE MOTORS ROADSTER you selected\./);
    expect(within(vin).getByRole("link").getAttribute("href")).toBe("https://www.nhtsa.gov/recalls");
  });

  it("accepted explanation: AI label above the official text; fallback: no AI label", () => {
    const accepted = card({ explanation: { status: "accepted", model: "m", prompt_version: "p",
      sentences: [{ text: "A bolt may loosen.", source_fields: ["summary"], source_spans: ["Bolt may loosen."] }] } });
    const { container, unmount } = one(accepted);
    const text = container.textContent!;
    expect(text.indexOf(AI_LABEL)).toBeGreaterThan(-1);
    expect(text.indexOf(AI_LABEL)).toBeLessThan(text.indexOf("Official NHTSA text"));
    unmount();
    one(card({ explanation: { status: "fallback", sentences: [], model: null, prompt_version: null } }));
    expect(screen.queryByText(/AI-generated/)).toBeNull();
    expect(screen.getByText("Official NHTSA text")).toBeTruthy();
  });

  it("long official text stays visible and expands with an accessible button", () => {
    one(card({ summary: "x".repeat(800) }));
    const btn = screen.getByRole("button", { name: "Show full official text" });
    expect(btn.getAttribute("aria-expanded")).toBe("false");
    expect(document.querySelector(".official-text")!.textContent!.length).toBeGreaterThan(300);
    fireEvent.click(btn);
    expect(screen.getByRole("button", { name: "Show less" }).getAttribute("aria-expanded")).toBe("true");
    expect(document.querySelector(".official-text")!.textContent).toBe("x".repeat(800));
  });

  it("one card per campno; empty list says what it means", () => {
    const { unmount } = render(<RecallCards campaigns={[card({}), card({}), card({ campno: "19V1" })]} vehicle={V} />);
    expect(screen.getAllByTestId("recall-card")).toHaveLength(2);
    expect(screen.getAllByTestId("recall-vin")).toHaveLength(2);
    unmount();
    render(<RecallCards campaigns={[]} vehicle={V} />);
    expect(screen.getByText(NO_RECALLS_TEXT)).toBeTruthy();
  });

  it("never renders the forbidden phrases (PRD F1.6)", () => {
    const { container } = render(<RecallCards campaigns={[card({ park_it: true, park_outside: true })]} vehicle={V} />);
    for (const bad of [/your car is affected/i, /your recall is unrepaired/i, /your car is safe/i]) {
      expect(container.textContent).not.toMatch(bad);
    }
  });
});

describe("vehicle page", () => {
  it("shows the fixture's three cards with their banners", async () => {
    render(
      <MemoryRouter initialEntries={["/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017"]}>
        <VehiclePage />
      </MemoryRouter>,
    );
    expect(await screen.findAllByTestId("recall-card")).toHaveLength(3);
    expect(screen.getAllByTestId("banner-park-it")).toHaveLength(1);
    expect(screen.getAllByTestId("banner-park-outside")).toHaveLength(1);
    expect(screen.getAllByText(AI_LABEL)).toHaveLength(1);
  });
});
