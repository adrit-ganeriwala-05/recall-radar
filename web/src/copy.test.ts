// Fails if any UI source file contains a banned claim word (CLAUDE.md §1).
import { describe, expect, it } from "vitest";

const BANNED: RegExp[] = [
  /\bdefective\b/i,
  /\bdangerous\b/i,
  /will be recalled/i,
  /predicts? recalls?/i,
  /lives saved/i,
  /crashes prevented/i,
  /\bowners\b/i, // we count distinct complaints
];

const SOURCES = import.meta.glob(["./**/*.{ts,tsx,css}", "../index.html", "!./**/*.test.{ts,tsx}", "!./contracts.gen.ts"], {
  eager: true,
  query: "?raw",
  import: "default",
}) as Record<string, string>;

describe("UI copy", () => {
  it("scans the UI sources", () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(10);
  });

  it.each(Object.entries(SOURCES))("%s has no banned words", (_file, text) => {
    const hits = BANNED.filter((re) => re.test(text)).map(String);
    expect(hits).toEqual([]);
  });
});
