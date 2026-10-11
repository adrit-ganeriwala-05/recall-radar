"""F7 (PRD_v2 §4): everyday-symptom search. Text and phrase search, nothing else.

There is no model, no embedding and no request-time call here. A query is matched to reviewed
concepts by words and phrases, and a concept is matched to complaint excerpts by words and
phrases plus the complaint's NHTSA component system. The same rules run in the browser; the
spec for that port is docs/METHOD_NOTES.md §12 and the functions below are its reference.

Reviewed inputs (owner B):
- review/symptom_concepts.csv — one row per concept: the component systems a complaint must be
  filed under, and groups of phrases that must ALL be present (`require_all`: groups separated
  by ";", phrases inside a group by "|"), plus phrases that rule the concept out (`exclude`).
- review/symptom_aliases.csv — everyday phrase -> concept id.

Text rules (the whole of the "simple inflections" handling):
1. lower-case; drop apostrophes; every other non-alphanumeric character becomes a space;
2. negative contractions become the token "not" (wont, doesnt, cant, ...);
3. stopwords are removed (STOPWORDS below; "no" and "not" are kept);
4. each token is stemmed by `stem` (strip one of ing/ed/es/s/e, then undouble a final consonant);
5. a phrase matches when its tokens appear in order with at most SLOP other tokens between
   neighbours.

The tables this module writes (`symptom_concept`, `symptom_alias`) are a copy of the current
review files. They are never read by the detector, the matcher, the evaluation or the replay.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONCEPTS_CSV = REPO_ROOT / "review" / "symptom_concepts.csv"
ALIASES_CSV = REPO_ROOT / "review" / "symptom_aliases.csv"
METHOD_LABEL = "Text and phrase search in the current cached snapshot. A match is not a diagnosis."
SLOP = 2

NEGATIONS = frozenset(
    "wont doesnt didnt dont cant cannot isnt wasnt arent werent wouldnt couldnt shouldnt hasnt havent hadnt never".split()
)
STOPWORDS = frozenset(
    """a an the my our your his her their its it i we you he she they me us this that these those there here
    is are was were be been being am do does did has have had will would could can should may might must shall
    to of in on at by for with from into onto up out as and or but if then than so very just also too
    when while car vehicle truck suv""".split()
)
_NON_WORD = re.compile(r"[^a-z0-9]+")
_KEEP_DOUBLE = frozenset("lsfz")  # stall, press, stiff, buzz keep their double letter


def stem(token: str) -> str:
    """Strip one common ending. Deliberately small: every rule is listed here and in the TS port."""
    if len(token) > 3:
        for suffix in ("ing", "ed", "es", "s", "e"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 3 and not (suffix == "s" and token.endswith("ss")):
                token = token[: -len(suffix)]
                if suffix in ("ing", "ed") and len(token) >= 4 and token[-1] == token[-2] and token[-1] not in _KEEP_DOUBLE:
                    token = token[:-1]  # stopped -> stop, shutting -> shut
                break
    return token


def tokens(text: str) -> list[str]:
    """Normalised, stemmed tokens of a text, in order, without stopwords."""
    words = _NON_WORD.sub(" ", text.lower().replace("'", "").replace("’", "")).split()
    out = []
    for w in words:
        if w in NEGATIONS:
            out.append("not")
        elif w not in STOPWORDS:
            out.append(stem(w))
    return out


def phrase_in(doc: Sequence[str], phrase: Sequence[str], slop: int = SLOP) -> bool:
    """True when `phrase` occurs in `doc` in order, with at most `slop` tokens between neighbours."""
    if not phrase:
        return False
    first = phrase[0]
    for start, tok in enumerate(doc):
        if tok != first:
            continue
        pos, ok = start, True
        for want in phrase[1:]:
            window = doc[pos + 1 : pos + 2 + slop]
            if want not in window:
                ok = False
                break
            pos = pos + 1 + window.index(want)
        if ok:
            return True
    return False


@dataclass(frozen=True)
class Concept:
    id: str
    label: str
    comp_systems: tuple[str, ...]
    require_all: tuple[tuple[str, ...], ...]  # every group needs one of its phrases
    exclude: tuple[str, ...]

    @property
    def terms(self) -> tuple[str, ...]:
        """Flat list of every phrase, for highlighting (contract field `terms`)."""
        return tuple(dict.fromkeys(p for group in self.require_all for p in group))

    def text_matches(self, toks: Sequence[str]) -> bool:
        if any(phrase_in(toks, tokens(p)) for p in self.exclude):
            return False
        return all(any(phrase_in(toks, tokens(p)) for p in group) for group in self.require_all)

    def matched_terms(self, toks: Sequence[str]) -> list[str]:
        return [p for group in self.require_all for p in group if phrase_in(toks, tokens(p))]

    def doc_matches(self, toks: Sequence[str], comp_systems: Iterable[str]) -> bool:
        """A complaint is this concept when it is filed under one of the concept's systems and its text matches."""
        if self.comp_systems and not set(comp_systems) & set(self.comp_systems):
            return False
        return self.text_matches(toks)


@dataclass(frozen=True)
class Alias:
    phrase: str
    concept_id: str


def _split(cell: str, sep: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in cell.split(sep) if p.strip())


def load_concepts(path: Path | str = CONCEPTS_CSV) -> list[Concept]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = [
        Concept(
            id=r["concept_id"].strip(), label=r["label"].strip(), comp_systems=_split(r["comp_systems"], "|"),
            require_all=tuple(_split(g, "|") for g in r["require_all"].split(";") if g.strip()),
            exclude=_split(r["exclude"], "|"),
        )
        for r in rows
    ]  # fmt: skip
    ids = [c.id for c in out]
    if len(set(ids)) != len(ids) or any(not c.require_all for c in out):
        raise ValueError("symptom_concepts.csv: duplicate concept id or a concept without required phrases")
    return out


def load_aliases(path: Path | str = ALIASES_CSV, concepts: Sequence[Concept] | None = None) -> list[Alias]:
    with open(path, newline="", encoding="utf-8") as f:
        out = [Alias(r["phrase"].strip(), r["concept_id"].strip()) for r in csv.DictReader(f)]
    if concepts is not None:
        unknown = sorted({a.concept_id for a in out} - {c.id for c in concepts})
        if unknown:
            raise ValueError(f"symptom_aliases.csv names unknown concepts: {unknown}")
    if len({a.phrase.lower() for a in out}) != len(out):
        raise ValueError("symptom_aliases.csv: a phrase is listed twice")
    return out


def concepts_for_query(query: str, concepts: Sequence[Concept], aliases: Sequence[Alias]) -> list[str]:
    """Concept ids a typed query stands for: reviewed aliases first, then the concepts' own phrases."""
    toks = tokens(query)
    hit = {a.concept_id for a in aliases if phrase_in(toks, tokens(a.phrase))}
    hit |= {c.id for c in concepts if c.text_matches(toks)}
    return [c.id for c in concepts if c.id in hit]


@dataclass(frozen=True)
class Hit:
    doc_index: int
    concept_ids: tuple[str, ...]  # empty for a plain text match
    matched_terms: tuple[str, ...]


def search(query: str, docs: Sequence[tuple[str, Sequence[str]]], concepts: Sequence[Concept], aliases: Sequence[Alias]) -> list[Hit]:
    """Search `docs` (excerpt, component systems), which the caller passes newest first; order is kept.

    With a concept for the query: every doc that is that concept. With none: docs that contain
    every word of the query. An empty or stopword-only query finds nothing.
    """
    q = tokens(query)
    if not q:
        return []
    by_id = {c.id: c for c in concepts}
    wanted = [by_id[i] for i in concepts_for_query(query, concepts, aliases)]
    hits = []
    for i, (excerpt, systems) in enumerate(docs):
        toks = tokens(excerpt)
        if wanted:
            matched = [c for c in wanted if c.doc_matches(toks, systems)]
            if matched:
                terms = tuple(dict.fromkeys(t for c in matched for t in c.matched_terms(toks)))
                hits.append(Hit(i, tuple(c.id for c in matched), terms))
        elif all(t in toks for t in q):
            hits.append(Hit(i, (), tuple(dict.fromkeys(q))))
    return hits


def write_tables(db_path: Path | str, concepts: Sequence[Concept], aliases: Sequence[Alias]) -> tuple[int, int]:
    """(Re)create `symptom_concept` and `symptom_alias` in B's own DuckDB file. Returns the row counts."""
    import duckdb

    con = duckdb.connect(str(db_path))
    try:
        con.execute("DROP TABLE IF EXISTS symptom_concept")
        con.execute("DROP TABLE IF EXISTS symptom_alias")
        con.execute(
            """CREATE TABLE symptom_concept (id VARCHAR PRIMARY KEY, label VARCHAR, comp_systems VARCHAR[],
                                              terms VARCHAR[], require_all VARCHAR[][], exclude VARCHAR[])"""
        )
        con.execute("CREATE TABLE symptom_alias (phrase VARCHAR PRIMARY KEY, concepts VARCHAR[])")
        con.executemany(
            "INSERT INTO symptom_concept VALUES (?, ?, ?, ?, ?, ?)",
            [[c.id, c.label, list(c.comp_systems), list(c.terms), [list(g) for g in c.require_all], list(c.exclude)] for c in concepts],
        )
        con.executemany("INSERT INTO symptom_alias VALUES (?, ?)", [[a.phrase, [a.concept_id]] for a in aliases])
        return len(concepts), len(aliases)
    finally:
        con.close()


PARITY_JSON = REPO_ROOT / "review" / "symptom_parity.json"
PARITY_DOCS = [  # made-up complaint texts (no real complaint is copied here), with their component systems
    ("Brakes squeal loudly when stopping.", ["SERVICE BRAKES"]),
    ("Grinding noise from the rear brakes since last week.", ["SERVICE BRAKES, HYDRAULIC"]),
    ("Brake pedal went to the floor, the car would not stop.", ["SERVICE BRAKES"]),
    ("Engine makes a squealing noise near the brakes.", ["ENGINE"]),
    ("THE STEERING WHEEL SHAKES AT 60 MPH.", ["STEERING"]),
    ("Lost power steering and the wheel was very hard to turn.", ["STEERING"]),
    ("The driver door won't lock with the key fob.", ["LATCHES/LOCKS/LINKAGES"]),
    ("Rear door flew open while driving on the highway.", ["LATCHES/LOCKS/LINKAGES"]),
    ("Engine shut off while driving on the freeway and restarted later.", ["ENGINE"]),
    ("Car will not start in the morning; it cranks but does not start.", ["ELECTRICAL SYSTEM"]),
    ("The radio display flickers on cold mornings.", ["ELECTRICAL SYSTEM"]),
    ("Door does not always fully lock at night.", ["STRUCTURE"]),
]
PARITY_FREE_TEXT = ["radio flickering", "sunroof leaks", "   ", "the of", "My door DOESN'T lock, properly!", "won\u2019t start"]


def parity(concepts: Sequence[Concept], aliases: Sequence[Alias], eval_csv: Path | str | None = None) -> dict:
    """Inputs and expected outputs for the browser port: the TypeScript search must reproduce every case."""
    queries = [a.phrase for a in aliases] + PARITY_FREE_TEXT
    path = Path(eval_csv) if eval_csv else REPO_ROOT / "review" / "symptom_eval.csv"
    with open(path, newline="", encoding="utf-8") as f:
        queries += [r["query"] for r in csv.DictReader(f)]
    queries = list(dict.fromkeys(queries))
    return {
        "note": "Generated by `python -m recall_radar.b_v2.symptom_index --parity`. Do not edit. Every text is made up or a reviewed phrase.",
        "method_label": METHOD_LABEL,
        "slop": SLOP,
        "stopwords": sorted(STOPWORDS),
        "negations": sorted(NEGATIONS),
        "stem_suffixes": ["ing", "ed", "es", "s", "e"],
        "keep_double": sorted(_KEEP_DOUBLE),
        "tokens": [{"text": t, "tokens": tokens(t)} for t in [d for d, _ in PARITY_DOCS] + PARITY_FREE_TEXT],
        "queries": [{"query": q, "concepts": concepts_for_query(q, concepts, aliases)} for q in queries],
        "search": [
            {"query": q, "hits": [{"doc": h.doc_index, "concepts": list(h.concept_ids), "terms": list(h.matched_terms)} for h in search(q, PARITY_DOCS, concepts, aliases)]}
            for q in queries
        ],
        "docs": [{"excerpt": d, "comp_systems": s} for d, s in PARITY_DOCS],
    }


def parity_text(concepts: Sequence[Concept], aliases: Sequence[Alias]) -> str:
    import json

    return json.dumps(parity(concepts, aliases), indent=1, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write symptom_concept and symptom_alias into B's v2 tables file.")
    ap.add_argument("--out", help="DuckDB file for B's v2 tables (never A's database, never the serving database)")
    ap.add_argument("--parity", action="store_true", help="rewrite review/symptom_parity.json for the browser port")
    args = ap.parse_args(argv)
    concepts = load_concepts()
    aliases = load_aliases(concepts=concepts)
    if args.parity:
        PARITY_JSON.write_text(parity_text(concepts, aliases), encoding="utf-8")
        print(f"parity cases -> {PARITY_JSON}")
    if not args.out:
        return 0 if args.parity else 2
    n_c, n_a = write_tables(args.out, concepts, aliases)
    print(f"symptom tables -> {args.out}: {n_c} concepts, {n_a} aliases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
