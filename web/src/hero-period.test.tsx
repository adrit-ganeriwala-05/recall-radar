// The hero replay is labelled with the period it comes from (B's handoff 20261010-2035: the frozen rule
// fell back to a development case). Expected text is written out here, not copied from format.ts.
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { heroPeriodNote } from "./format";
import ReplayPage from "./pages/ReplayPage";
import SelectorPage from "./pages/SelectorPage";

const DEV =
  "Development-period case: no held-out case qualified under the frozen hero rule, so this example comes " +
  "from the development years, which were used to choose the detector settings.";

describe("hero period label", () => {
  it("says development or held-out in plain words", () => {
    expect(heroPeriodNote("development")).toBe(DEV);
    expect(heroPeriodNote("held_out")).toBe("Held-out-period case, chosen by the hero rule frozen before the held-out run.");
  });

  it("the landing hero card carries it (fixture hero E-0412 is a development case)", async () => {
    render(
      <MemoryRouter>
        <SelectorPage />
      </MemoryRouter>,
    );
    const label = await screen.findByTestId("hero-period");
    expect(label.textContent).toBe(DEV);
    expect(label.closest("aside")?.textContent).toMatch(/Open replay E-0412/);
  });

  function renderAt(path: string) {
    return render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/replay/:episodeId" element={<ReplayPage />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it("the hero's replay page carries it", async () => {
    renderAt("/replay/E-0412");
    expect((await screen.findByTestId("hero-period")).textContent).toBe(DEV);
  });

  it("a replay that is not the hero does not claim to be one", async () => {
    renderAt("/replay/E-9999");
    await screen.findByText(/./, { selector: ".state" });
    expect(screen.queryByTestId("hero-period")).toBeNull();
  });
});
