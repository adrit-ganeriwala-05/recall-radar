// PRD v2 F4: My car — one key, readback-verified save, guarded storage, redirect only on a bare first "/".
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MyCarControls } from "./components/MyCar";
import { forgetMyCar, MYCAR_KEY, readMyCar, saveMyCar } from "./mycar";
import SelectorPage, { resetSavedCarCheck } from "./pages/SelectorPage";

const V = { make: "EXAMPLE MOTORS", model: "ROADSTER", model_year: 2017 };
beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("storage", () => {
  it("saves exactly {v, make, model, year} under one key and reads it back", () => {
    expect(saveMyCar("EXAMPLE MOTORS", "ROADSTER", 2017)).toBe("saved");
    expect(Object.keys(localStorage)).toEqual([MYCAR_KEY]);
    expect(JSON.parse(localStorage.getItem(MYCAR_KEY)!)).toEqual({ v: 1, make: "EXAMPLE MOTORS", model: "ROADSTER", year: 2017 });
    expect(readMyCar()).toEqual({ car: { v: 1, make: "EXAMPLE MOTORS", model: "ROADSTER", year: 2017 }, problem: null });
  });

  it.each([
    ["{not json", "malformed"],
    [JSON.stringify({ v: 2, make: "A", model: "B", year: 2017 }), "wrong version"],
    [JSON.stringify({ v: 1, make: "A", year: 2017 }), "missing model"],
    [JSON.stringify({ v: 1, make: "A", model: "B", year: "2017" }), "year not a number"],
  ])("%s (%s) is ignored with a short message", (raw) => {
    localStorage.setItem(MYCAR_KEY, raw);
    const r = readMyCar();
    expect(r.car).toBeNull();
    expect(r.problem).toMatch(/ignored/);
  });

  it("getItem / setItem throwing never breaks the app", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(readMyCar().car).toBeNull();
    vi.restoreAllMocks();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("quota"); });
    expect(saveMyCar("A", "B", 2017)).toBe("failed");
  });

  it("forget removes only our key, never clear()", () => {
    localStorage.setItem("someone-else", "x");
    saveMyCar("A", "B", 2017);
    const clear = vi.spyOn(Storage.prototype, "clear");
    forgetMyCar();
    expect(clear).not.toHaveBeenCalled();
    expect(localStorage.getItem(MYCAR_KEY)).toBeNull();
    expect(localStorage.getItem("someone-else")).toBe("x");
  });
});

describe("controls", () => {
  const show = () =>
    render(
      <MemoryRouter>
        <MyCarControls vehicle={V} />
      </MemoryRouter>,
    );
  it('"Saved" only after a matching readback; otherwise "Couldn\'t save in this browser"', () => {
    show();
    fireEvent.click(screen.getByRole("button", { name: "Remember this car" }));
    expect(screen.getByTestId("mycar-status").textContent).toBe("Saved");
    expect(screen.getByRole("link", { name: "Change car" }).getAttribute("href")).toBe("/?change=1");
  });
  it("readback mismatch is reported as a failure", () => {
    vi.spyOn(Storage.prototype, "getItem").mockReturnValue("something else");
    show();
    fireEvent.click(screen.getByRole("button", { name: "Remember this car" }));
    expect(screen.getByTestId("mycar-status").textContent).toBe("Couldn't save in this browser");
  });
});

describe("redirect on the first bare '/' only", () => {
  function Where() {
    return <p data-testid="where">{useLocation().pathname + useLocation().search}</p>;
  }
  const app = (path: string) =>
    render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/" element={<SelectorPage />} />
          <Route path="/vehicle" element={<Where />} />
        </Routes>
      </MemoryRouter>,
    );

  it("opens the saved car when it resolves in the data", async () => {
    resetSavedCarCheck(true);
    saveMyCar("EXAMPLE MOTORS", "ROADSTER", 2017);
    app("/");
    expect((await screen.findByTestId("where")).textContent).toBe("/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017");
  });

  it("a vanished vehicle is ignored with a short message", async () => {
    resetSavedCarCheck(true);
    saveMyCar("EXAMPLE MOTORS", "ROADSTER", 2001);
    app("/");
    expect((await screen.findByTestId("mycar-note")).textContent).toMatch(/no longer in this data/);
  });

  it("a query (deep link or Change car) wins, and a second visit never redirects", async () => {
    resetSavedCarCheck(true);
    saveMyCar("EXAMPLE MOTORS", "ROADSTER", 2017);
    const { unmount } = app("/?change=1");
    await screen.findByTestId("promise");
    expect(screen.queryByTestId("where")).toBeNull();
    unmount();
    app("/"); // same session, second mount
    await screen.findByTestId("promise");
    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByTestId("where")).toBeNull();
  });
});
