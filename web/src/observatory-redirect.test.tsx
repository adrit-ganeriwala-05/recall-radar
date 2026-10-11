import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import ObservatoryRedirect, { OBSERVATORY_FILE } from "./ObservatoryRedirect";

vi.mock("./ObservatoryRedirect", async (orig) => {
  const real = await orig<typeof import("./ObservatoryRedirect")>();
  return { ...real, default: (props: { navigate?: (u: string) => void }) => (props.navigate ? real.default(props) : <p data-testid="observatory-route" />) };
});

// Imported after the mock so the App's route renders the marker instead of navigating jsdom.
const { default: App } = await import("./App");

describe("observatory redirect", () => {
  it("forwards to the static export file", () => {
    const navigate = vi.fn();
    render(<ObservatoryRedirect navigate={navigate} />);
    expect(navigate).toHaveBeenCalledWith("/observatory/index.html");
    expect(OBSERVATORY_FILE).toBe("/observatory/index.html");
    expect(screen.getByRole("link", { name: "open the presentation" }).getAttribute("href")).toBe("/observatory/index.html");
  });

  it.each(["/observatory", "/observatory/"])("route %s is handled by the redirect", (path) => {
    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("observatory-route")).toBeTruthy();
  });

  it("does not catch /observatory/index.html (no loop when the export is missing)", () => {
    render(
      <MemoryRouter initialEntries={["/observatory/index.html"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.queryByTestId("observatory-route")).toBeNull();
    expect(screen.getByText("Page not found")).toBeTruthy();
  });
});
