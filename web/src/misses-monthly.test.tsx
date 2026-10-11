// PROJECT_SPEC §7/§8: every miss is listed with its monthly counts. Each vehicle in a results row links
// to its complaint group for the investigation's component system (the issue page: monthly counts
// against the baseline). Expected hrefs and texts are written out here from the fixtures.
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";
import IssueForPage, { issueForHref } from "./pages/IssueForPage";
import { Results } from "./pages/ResultsPage";
import { resultsFixture } from "./test/fixtures";

describe("misses link to their monthly counts", () => {
  it("builds the link from vehicle + investigated system", () => {
    expect(issueForHref({ make: "SAMPLE AUTO", model: "HATCH", model_year: 2016 }, "AIR BAGS")).toBe(
      "/issue-for?make=SAMPLE+AUTO&model=HATCH&year=2016&system=AIR+BAGS",
    );
  });

  it("every vehicle in the misses list is a link to that vehicle's counts for the investigated system", () => {
    render(
      <MemoryRouter>
        <Results data={resultsFixture("development")} />
      </MemoryRouter>,
    );
    const misses = screen.getByTestId("misses-list");
    const links = within(misses).getAllByRole("link", { name: "2016 SAMPLE AUTO HATCH" });
    expect(links.map((a) => a.getAttribute("href")).sort()).toEqual([
      "/issue-for?make=SAMPLE+AUTO&model=HATCH&year=2016&system=AIR+BAGS",
      "/issue-for?make=SAMPLE+AUTO&model=HATCH&year=2016&system=ELECTRICAL+SYSTEM",
    ]);
  });

  function Where() {
    const loc = useLocation();
    return <p data-testid="where">{loc.pathname}</p>;
  }

  function renderAt(path: string) {
    return render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/issue-for" element={<IssueForPage />} />
          <Route path="/issue/:groupId" element={<Where />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it("opens the issue page of the vehicle's group for that system", async () => {
    renderAt("/issue-for?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017&system=STEERING");
    expect((await screen.findByTestId("where")).textContent).toBe("/issue/g_6bc38243bb0a");
  });

  it("says plainly when no complaint was filed under that system, and links the vehicle page", async () => {
    renderAt("/issue-for?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017&system=AIR+BAGS");
    const msg = await screen.findByText(/were filed under the component name “AIR BAGS”/);
    expect(msg.textContent).toMatch(/no monthly count to show/);
    expect(screen.getByRole("link", { name: "vehicle page" }).getAttribute("href")).toBe(
      "/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017",
    );
  });
  it("a vehicle with no complaints at all gets the same plain message, not a dead end", async () => {
    renderAt("/issue-for?make=NO+SUCH&model=CAR&year=2016&system=AIR+BAGS");
    const msg = await screen.findByText(/No complaints about this vehicle are in the data range/);
    expect(msg.textContent).toMatch(/no monthly count to show for “\s*AIR BAGS”/);
  });
});
