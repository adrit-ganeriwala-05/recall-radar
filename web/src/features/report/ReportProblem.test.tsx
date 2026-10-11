// Owner: D. F5 tests (PRD_v2 §4 F5). Expected draft texts are written by hand, not produced by the code.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReportProblem, NHTSA_REPORT_URL, SUBMIT_NOTE } from "./ReportProblem";
import { buildDraft, EMPTY_ANSWERS, type ReportAnswers } from "./template";

const SYNTH = "ZZQ-SYNTH-7741";
const JETTA = { make: "VOLKSWAGEN", model: "JETTA", model_year: 2019 };

function answers(over: Partial<ReportAnswers>): ReportAnswers {
  return { ...EMPTY_ANSWERS, ...over };
}

describe("buildDraft (deterministic template)", () => {
  it("uses only the supplied facts, in a fixed order", () => {
    const text = buildDraft(
      answers({
        make: "VOLKSWAGEN", model: "JETTA", year: "2019",
        dateMode: "exact", exactDate: "2024-03-15",
        mileageMode: "number", mileage: "42000",
        description: "The car lost power on the highway.",
        frequency: "repeatedly", crash: "no", fire: "no", injury: "unknown",
      }),
    );
    expect(text).toBe(
      [
        "Vehicle: 2019 VOLKSWAGEN JETTA",
        "Date of the incident: 2024-03-15",
        "Mileage at the time: 42000 miles",
        "How often it happened: repeatedly",
        "Crash: no",
        "Fire: no",
        "Injury: unknown",
        "",
        "What happened, in my words:",
        "The car lost power on the highway.",
      ].join("\n"),
    );
  });

  it("keeps an approximate date approximate", () => {
    expect(buildDraft(answers({ dateMode: "approximate", approxMonth: "3", approxYear: "2024" }))).toBe(
      "Date of the incident: approximately March 2024",
    );
    expect(buildDraft(answers({ dateMode: "approximate", approxMonth: "", approxYear: "2023" }))).toBe(
      "Date of the incident: approximately 2023",
    );
  });

  it("writes unknown only when chosen, never turns it into no, and leaves out unanswered questions", () => {
    expect(buildDraft(answers({ crash: "unknown" }))).toBe("Crash: unknown");
    expect(buildDraft(answers({ crash: "no" }))).toBe("Crash: no");
    expect(buildDraft(answers({ dateMode: "unknown", mileageMode: "unknown", frequency: "unknown" }))).toBe(
      ["Date of the incident: unknown", "Mileage at the time: unknown", "How often it happened: unknown"].join("\n"),
    );
    expect(buildDraft(answers({}))).toBe("");
  });

  it("copies the person's words verbatim, without filtering", () => {
    const words = "  It felt  defective and dangerous!\nTwice.  ";
    expect(buildDraft(answers({ description: words }))).toBe(`\nWhat happened, in my words:\n${words}`);
  });

  it("drops a mileage that is not digits instead of guessing", () => {
    expect(buildDraft(answers({ mileageMode: "number", mileage: "about 40k" }))).toBe("");
  });
});

// ---------------------------------------------------------------- component helpers
function describeStep(text = "Brakes made a grinding noise.") {
  fireEvent.change(screen.getByLabelText(/What happened\?/), { target: { value: text } });
}
function toReview() {
  fireEvent.click(screen.getByRole("button", { name: "Review the draft" }));
}
function draftBox(): HTMLTextAreaElement {
  return screen.getByLabelText("Review and edit the draft") as HTMLTextAreaElement;
}
function pick(groupName: string, option: string) {
  const group = screen.getByRole("group", { name: new RegExp(groupName) });
  fireEvent.click(within(group).getByLabelText(option));
}

describe("ReportProblem", () => {
  it("prefills the vehicle and has no VIN, name, email, phone, address, file or payment fields", () => {
    const { container } = render(<ReportProblem initialVehicle={JETTA} />);
    expect((screen.getByLabelText("Make") as HTMLInputElement).value).toBe("VOLKSWAGEN");
    expect((screen.getByLabelText("Model") as HTMLInputElement).value).toBe("JETTA");
    expect((screen.getByLabelText("Year") as HTMLInputElement).value).toBe("2019");
    const labels = Array.from(container.querySelectorAll("label, legend")).map((l) => l.textContent ?? "");
    for (const bad of [/\bVIN\b/, /\bname\b/i, /e-?mail/i, /phone/i, /address/i, /card|payment/i]) {
      expect(labels.filter((t) => bad.test(t) && !/Don't include/.test(t))).toEqual([]);
    }
    expect(container.querySelector('input[type="file"]')).toBeNull();
  });

  it("has no default on crash, fire and injury, and the draft keeps Unknown distinct from No", () => {
    render(<ReportProblem initialVehicle={JETTA} />);
    for (const g of ["crash", "fire", "anyone injured"]) {
      const group = screen.getByRole("group", { name: new RegExp(g) });
      expect(within(group).getAllByRole("radio").some((r) => (r as HTMLInputElement).checked)).toBe(false);
    }
    describeStep();
    pick("crash", "Unknown");
    pick("fire", "No");
    toReview();
    expect(draftBox().value).toContain("Crash: unknown");
    expect(draftBox().value).toContain("Fire: no");
    expect(draftBox().value).not.toContain("Injury");
  });

  it("keeps manual edits across step navigation", () => {
    render(<ReportProblem />);
    describeStep();
    toReview();
    fireEvent.change(draftBox(), { target: { value: "My own edited text" } });
    fireEvent.click(screen.getByRole("button", { name: "Back to my answers" }));
    pick("fire", "Yes"); // a changed answer must not silently overwrite the edit
    toReview();
    expect(draftBox().value).toBe("My own edited text");
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    fireEvent.click(screen.getByRole("button", { name: "Back to the draft" }));
    expect(draftBox().value).toBe("My own edited text");
  });

  it("asks before regenerating over manual edits", () => {
    render(<ReportProblem initialVehicle={JETTA} />);
    describeStep("Door would not lock.");
    toReview();
    fireEvent.change(draftBox(), { target: { value: "edited" } });
    fireEvent.click(screen.getByRole("button", { name: "Regenerate from my answers" }));
    expect(draftBox().value).toBe("edited");
    fireEvent.click(screen.getByRole("button", { name: "Keep my edits" }));
    expect(draftBox().value).toBe("edited");
    fireEvent.click(screen.getByRole("button", { name: "Regenerate from my answers" }));
    fireEvent.click(screen.getByRole("button", { name: "Replace my edits" }));
    expect(draftBox().value).toBe("Vehicle: 2019 VOLKSWAGEN JETTA\n\nWhat happened, in my words:\nDoor would not lock.");
  });

  it("clear draft resets every answer and the draft", () => {
    render(<ReportProblem initialVehicle={JETTA} />);
    fireEvent.change(screen.getByLabelText("Make"), { target: { value: "FORD" } });
    describeStep("something");
    pick("crash", "Yes");
    toReview();
    fireEvent.click(screen.getByRole("button", { name: "Clear draft" }));
    expect((screen.getByLabelText("Make") as HTMLInputElement).value).toBe("VOLKSWAGEN");
    expect((screen.getByLabelText(/What happened\?/) as HTMLTextAreaElement).value).toBe("");
    const crash = screen.getByRole("group", { name: /crash/ });
    expect(within(crash).getAllByRole("radio").some((r) => (r as HTMLInputElement).checked)).toBe(false);
  });

  it("never claims the complaint was submitted", () => {
    const { container } = render(<ReportProblem initialVehicle={JETTA} />);
    const seen: string[] = [container.textContent ?? ""];
    describeStep();
    toReview();
    seen.push(container.textContent ?? "");
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    seen.push(container.textContent ?? "");
    expect(screen.getByText("Draft ready")).toBeTruthy();
    expect(screen.getByText(SUBMIT_NOTE)).toBeTruthy();
    for (const t of seen) {
      expect(t.replace(SUBMIT_NOTE, "")).not.toMatch(/submitted|confirmation (number|code)/i);
    }
  });

  it("links to NHTSA in a new tab with noopener noreferrer, even before copying", () => {
    render(<ReportProblem />);
    describeStep();
    toReview();
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    const link = screen.getByRole("link", { name: "Continue to NHTSA" });
    expect(link.getAttribute("href")).toBe(NHTSA_REPORT_URL);
    expect(link.getAttribute("href")).toBe("https://www.nhtsa.gov/report-a-safety-problem");
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });

  describe("copy", () => {
    const original = Object.getOwnPropertyDescriptor(navigator, "clipboard");
    afterEach(() => {
      if (original) Object.defineProperty(navigator, "clipboard", original);
      else delete (navigator as { clipboard?: unknown }).clipboard;
    });
    function setClipboard(value: unknown) {
      Object.defineProperty(navigator, "clipboard", { value, configurable: true });
    }
    async function goCopy() {
      render(<ReportProblem initialVehicle={JETTA} />);
      describeStep("Engine stalled.");
      toReview();
      fireEvent.click(screen.getByRole("button", { name: "Continue" }));
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Copy draft" }));
      });
    }

    it('says "Copied" only after the clipboard write resolves', async () => {
      const writeText = vi.fn().mockResolvedValue(undefined);
      setClipboard({ writeText });
      await goCopy();
      expect(writeText).toHaveBeenCalledWith("Vehicle: 2019 VOLKSWAGEN JETTA\n\nWhat happened, in my words:\nEngine stalled.");
      expect(screen.getByText("Copied")).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Select all and copy" })).toBeNull();
    });

    it("falls back to a selectable text area when the write is rejected", async () => {
      setClipboard({ writeText: vi.fn().mockRejectedValue(new Error("denied")) });
      await goCopy();
      expect(screen.queryByText("Copied")).toBeNull();
      const box = screen.getByLabelText("Draft text to copy") as HTMLTextAreaElement;
      expect(box.value).toContain("Engine stalled.");
      expect(screen.getByRole("button", { name: "Select all and copy" })).toBeTruthy();
      expect(screen.getByRole("link", { name: "Continue to NHTSA" })).toBeTruthy();
    });

    it("falls back when there is no clipboard API", async () => {
      setClipboard(undefined);
      await goCopy();
      expect(screen.queryByText("Copied")).toBeNull();
      expect(screen.getByLabelText("Draft text to copy")).toBeTruthy();
    });
  });

  describe("privacy: the synthetic marker never leaves React memory", () => {
    let spies: ReturnType<typeof vi.fn>[] = [];
    beforeEach(() => {
      localStorage.clear();
      sessionStorage.clear();
      spies = [];
    });
    afterEach(() => vi.restoreAllMocks());

    it(`${SYNTH} is absent from storage, cookies, the URL, network calls and the console`, async () => {
      const fetchSpy = vi.fn().mockResolvedValue(new Response("{}"));
      vi.stubGlobal("fetch", fetchSpy);
      const xhrOpen = vi.spyOn(XMLHttpRequest.prototype, "open");
      const xhrSend = vi.spyOn(XMLHttpRequest.prototype, "send");
      const beacon = vi.fn().mockReturnValue(true);
      Object.defineProperty(navigator, "sendBeacon", { value: beacon, configurable: true });
      const consoles = (["log", "info", "warn", "error", "debug"] as const).map((m) =>
        vi.spyOn(console, m).mockImplementation(() => {}),
      );
      const setItem = vi.spyOn(Storage.prototype, "setItem");
      const writeText = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
      spies = [fetchSpy, beacon];

      render(<ReportProblem initialVehicle={JETTA} />);
      fireEvent.change(screen.getByLabelText("Model"), { target: { value: `JETTA ${SYNTH}` } });
      describeStep(`It happened near ${SYNTH} twice.`);
      pick("crash", "No");
      toReview();
      fireEvent.change(draftBox(), { target: { value: `${draftBox().value}\nedit ${SYNTH}` } });
      fireEvent.click(screen.getByRole("button", { name: "Continue" }));
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Copy draft" }));
      });
      // the only place the text may go is the clipboard the person asked for
      expect(writeText.mock.calls[0][0]).toContain(SYNTH);

      const stored = [localStorage, sessionStorage].flatMap((s) =>
        Object.keys(s).flatMap((k) => [k, s.getItem(k) ?? ""]),
      );
      expect(stored.join("|")).not.toContain(SYNTH);
      expect(setItem).not.toHaveBeenCalled();
      expect(document.cookie).not.toContain(SYNTH);
      expect(window.location.href).not.toContain(SYNTH);
      expect(window.history.state === null || !JSON.stringify(window.history.state).includes(SYNTH)).toBe(true);
      for (const s of spies) expect(s).not.toHaveBeenCalled();
      expect(xhrOpen).not.toHaveBeenCalled();
      expect(xhrSend).not.toHaveBeenCalled();
      for (const c of consoles) {
        expect(c.mock.calls.flat().map(String).join("|")).not.toContain(SYNTH);
      }
    });
  });
});
