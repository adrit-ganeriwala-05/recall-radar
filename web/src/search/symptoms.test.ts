// PRD v2 F7 parity: the browser search equals B's Python reference on review/symptom_parity.json
// (77 queries, 12 made-up documents, the word lists). Skips until those review files are on main (#27).
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { SymptomConcept } from "../contracts.gen";
import { conceptsForQuery, KEEP_DOUBLE, NEGATIONS, search, SLOP, STEM_SUFFIXES, STOPWORDS, tokens } from "./symptoms";

const REVIEW = resolve(__dirname, "../../../review");
const has = existsSync(resolve(REVIEW, "symptom_parity.json"));

function csv(name: string): Record<string, string>[] {
  const [head, ...rows] = readFileSync(resolve(REVIEW, name), "utf8").trim().split(/\r?\n/).map(parseLine);
  return rows.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ""])));
}
function parseLine(line: string): string[] {
  const out: string[] = [];
  let cur = "", q = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (q) {
      if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; } else if (ch === '"') q = false; else cur += ch;
    } else if (ch === '"') q = true;
    else if (ch === ",") { out.push(cur); cur = ""; } else cur += ch;
  }
  out.push(cur);
  return out;
}
const split = (s: string, sep: string) => s.split(sep).map((x) => x.trim()).filter(Boolean);

describe.skipIf(!has)("symptom search parity with B's Python reference", () => {
  const P = has ? JSON.parse(readFileSync(resolve(REVIEW, "symptom_parity.json"), "utf8")) : null;
  const concepts: SymptomConcept[] = has
    ? csv("symptom_concepts.csv").map((r) => {
        const require_all = r.require_all.split(";").filter((g) => g.trim()).map((g) => split(g, "|"));
        return { id: r.concept_id.trim(), label: r.label.trim(), comp_systems: split(r.comp_systems, "|"),
          terms: [...new Set(require_all.flat())], require_all, exclude: split(r.exclude, "|") };
      })
    : [];
  const byPhrase = new Map<string, string[]>();
  if (has) for (const r of csv("symptom_aliases.csv")) byPhrase.set(r.phrase.trim(), [...(byPhrase.get(r.phrase.trim()) ?? []), r.concept_id.trim()]);
  const idx = {
    concepts,
    aliases: [...byPhrase].map(([phrase, c]) => ({ phrase, concepts: c as [string, ...string[]] })),
  };

  it("word lists and settings are identical", () => {
    expect(P.slop).toBe(SLOP);
    expect([...STOPWORDS].sort()).toEqual([...P.stopwords].sort());
    expect([...NEGATIONS].sort()).toEqual([...P.negations].sort());
    expect([...STEM_SUFFIXES]).toEqual(P.stem_suffixes);
    expect([...KEEP_DOUBLE].sort()).toEqual([...P.keep_double].sort());
  });
  it("tokens", () => {
    for (const t of P.tokens) expect(tokens(t.text), t.text).toEqual(t.tokens);
  });
  it("query → concepts (77 queries)", () => {
    for (const q of P.queries) expect(conceptsForQuery(q.query, idx), q.query).toEqual(q.concepts);
  });
  it("search hits on the 12 made-up documents", () => {
    for (const s of P.search) {
      const got = search(s.query, P.docs, idx).map((h) => ({ doc: h.docIndex, concepts: h.conceptIds, terms: h.matchedTerms }));
      expect(got, s.query).toEqual(s.hits);
    }
  });
});
