// Owner: C. PRD v2 F7: browser port of B's symptom search (docs/METHOD_NOTES.md §12.4, recall_radar/b_v2/symptom_index.py).
// The typed query is only ever used here, in the page: never sent, stored, logged or put in a URL.
// review/symptom_parity.json pins this file to the Python reference (test: search/symptoms.test.ts).
import type { SymptomConcept, SymptomDoc, SymptomIndex } from "../contracts.gen";

export const SLOP = 2;
export const NEGATIONS = new Set(
  "wont doesnt didnt dont cant cannot isnt wasnt arent werent wouldnt couldnt shouldnt hasnt havent hadnt never".split(" "),
);
export const STOPWORDS = new Set(
  `a an the my our your his her their its it i we you he she they me us this that these those there here
  is are was were be been being am do does did has have had will would could can should may might must shall
  to of in on at by for with from into onto up out as and or but if then than so very just also too
  when while car vehicle truck suv`.split(/\s+/).filter(Boolean),
);
export const STEM_SUFFIXES = ["ing", "ed", "es", "s", "e"] as const;
export const KEEP_DOUBLE = new Set(["f", "l", "s", "z"]);

/** Rule 2: strip one common ending; after "ing"/"ed" undo a doubled letter (not l, s, f, z). */
export function stem(token: string): string {
  if (token.length > 3) {
    for (const suffix of STEM_SUFFIXES) {
      if (token.endsWith(suffix) && token.length - suffix.length >= 3 && !(suffix === "s" && token.endsWith("ss"))) {
        token = token.slice(0, -suffix.length);
        if ((suffix === "ing" || suffix === "ed") && token.length >= 4 && token.at(-1) === token.at(-2) && !KEEP_DOUBLE.has(token.at(-1)!)) {
          token = token.slice(0, -1);
        }
        break;
      }
    }
  }
  return token;
}

/** Rule 1: lower-case, drop apostrophes, other non-alphanumerics → space; negations → "not"; stopwords dropped. */
export function tokens(text: string): string[] {
  const words = text.toLowerCase().replace(/['’]/g, "").replace(/[^a-z0-9]+/g, " ").split(" ").filter(Boolean);
  const out: string[] = [];
  for (const w of words) {
    if (NEGATIONS.has(w)) out.push("not");
    else if (!STOPWORDS.has(w)) out.push(stem(w));
  }
  return out;
}

/** Rule 3: phrase tokens in order, at most SLOP other tokens between neighbours. */
export function phraseIn(doc: string[], phrase: string[], slop = SLOP): boolean {
  if (phrase.length === 0) return false;
  for (let start = 0; start < doc.length; start++) {
    if (doc[start] !== phrase[0]) continue;
    let pos = start;
    let ok = true;
    for (const want of phrase.slice(1)) {
      const window = doc.slice(pos + 1, pos + 2 + slop);
      const at = window.indexOf(want);
      if (at < 0) {
        ok = false;
        break;
      }
      pos = pos + 1 + at;
    }
    if (ok) return true;
  }
  return false;
}

const phraseTokens = new Map<string, string[]>();
const tok = (p: string) => {
  let t = phraseTokens.get(p);
  if (!t) phraseTokens.set(p, (t = tokens(p)));
  return t;
};

/** Rule 4 (text part). */
export function textMatches(c: SymptomConcept, toks: string[]): boolean {
  if ((c.exclude ?? []).some((p) => phraseIn(toks, tok(p)))) return false;
  return (c.require_all ?? []).length > 0 && (c.require_all ?? []).every((g) => g.some((p) => phraseIn(toks, tok(p))));
}

export function matchedTerms(c: SymptomConcept, toks: string[]): string[] {
  return (c.require_all ?? []).flat().filter((p) => phraseIn(toks, tok(p)));
}

/** Rule 4 (complaint): filed under one of the concept's systems (if it lists any) and the text matches. */
export function docMatches(c: SymptomConcept, toks: string[], systems: string[]): boolean {
  if (c.comp_systems.length && !systems.some((s) => c.comp_systems.includes(s))) return false;
  return textMatches(c, toks);
}

/** Rule 5: concepts of matching alias phrases plus concepts whose own rule matches the query; concepts-file order. */
export function conceptsForQuery(query: string, idx: Pick<SymptomIndex, "concepts" | "aliases">): string[] {
  const q = tokens(query);
  const hit = new Set<string>();
  for (const a of idx.aliases) if (phraseIn(q, tok(a.phrase))) a.concepts.forEach((c) => hit.add(c));
  for (const c of idx.concepts) if (textMatches(c, q)) hit.add(c.id);
  return idx.concepts.filter((c) => hit.has(c.id)).map((c) => c.id);
}

export type Hit = { docIndex: number; conceptIds: string[]; matchedTerms: string[] };

/** Rule 6. `docs` are newest first; that order is kept. */
export function search(
  query: string,
  docs: Pick<SymptomDoc, "excerpt" | "comp_systems">[],
  idx: Pick<SymptomIndex, "concepts" | "aliases">,
): Hit[] {
  const q = tokens(query);
  if (q.length === 0) return [];
  const byId = new Map(idx.concepts.map((c) => [c.id, c]));
  const wanted = conceptsForQuery(query, idx).map((id) => byId.get(id)!);
  const hits: Hit[] = [];
  docs.forEach((d, i) => {
    const toks = tokens(d.excerpt);
    if (wanted.length) {
      const matched = wanted.filter((c) => docMatches(c, toks, d.comp_systems));
      if (matched.length) {
        hits.push({ docIndex: i, conceptIds: matched.map((c) => c.id), matchedTerms: [...new Set(matched.flatMap((c) => matchedTerms(c, toks)))] });
      }
    } else if (q.every((t) => toks.includes(t))) {
      hits.push({ docIndex: i, conceptIds: [], matchedTerms: [...new Set(q)] });
    }
  });
  return hits;
}
