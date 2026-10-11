"""F7 evaluation (PRD_v2 F7.3): numbers for the symptom search, computed from the review files.

    python -m recall_radar.b_v2.symptom_eval [--db <baseline db>]

1. Query -> concept: for each of the queries in review/symptom_eval.csv, is the expected concept
   returned and is every hard negative absent?
2. Precision at 5: review/symptom_eval_judgments.csv holds B's relevance judgment (y/n, no text)
   for the top five results of every concept on the three sample vehicles. The sample is the three
   vehicles with the most distinct complaints; each vehicle's documents are its newest 2,000
   complaints, searched in the excerpt the site serves (at most 400 characters).
   With `--db`, the judged ids are checked against what the current rules return, so a rule change
   after the judgments were made is reported instead of silently reusing old judgments.

Nothing here is typed by hand into documents: quote this command's output.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from recall_radar.b_v2 import symptom_index as SI

EVAL_CSV = SI.REPO_ROOT / "review" / "symptom_eval.csv"
JUDGMENTS_CSV = SI.REPO_ROOT / "review" / "symptom_eval_judgments.csv"
SAMPLE_DOCS = 2000
TOP_K = 5


def query_results(concepts, aliases, path: Path | str = EVAL_CSV) -> list[dict]:
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            got = SI.concepts_for_query(r["query"], concepts, aliases)
            negatives = set(filter(None, r["hard_negative_concepts"].split("|")))
            out.append({
                "query": r["query"], "expected": r["expected_concept"], "got": got,
                "ok": r["expected_concept"] in got and not negatives & set(got),
                "exact": got == [r["expected_concept"]],
            })  # fmt: skip
    return out


def load_judgments(path: Path | str = JUDGMENTS_CSV) -> dict[tuple[str, str, int, str], dict[str, bool]]:
    """(make, model, model_year, concept) -> {odino: relevant}."""
    out: dict[tuple[str, str, int, str], dict[str, bool]] = defaultdict(dict)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["relevant"] not in ("y", "n"):
                raise ValueError(f"judgment must be y or n: {r}")
            out[(r["make"], r["model"], int(r["model_year"]), r["concept_id"])][r["odino"]] = r["relevant"] == "y"
    return dict(out)


def top_hits(con, concept: SI.Concept, make: str, model: str, year: int) -> list[str]:
    """Complaint ids of the concept's first TOP_K results among the vehicle's newest SAMPLE_DOCS excerpts."""
    from recall_radar.api.main import excerpt  # the text the site serves (A's function), not the stored text

    rows = con.execute(
        """SELECT d.odino, d.descr_redacted,
                  (SELECT list(DISTINCT r.comp_system) FROM complaint_row r WHERE r.odino = d.odino)
           FROM complaint_doc d
           WHERE d.make = ? AND d.model = ? AND d.model_year = ? AND d.descr_redacted IS NOT NULL
           ORDER BY d.avail_date DESC, CAST(d.odino AS BIGINT) DESC LIMIT ?""",
        [make, model, year, SAMPLE_DOCS],
    ).fetchall()
    hits = [str(o) for o, text, systems in rows if concept.doc_matches(SI.tokens(excerpt(text)), systems or [])]
    return hits[:TOP_K]


def report(db: str | None = None) -> tuple[list[str], bool]:
    concepts = SI.load_concepts()
    aliases = SI.load_aliases(concepts=concepts)
    lines, clean = [], True

    results = query_results(concepts, aliases)
    verbatim = {a.phrase.lower() for a in aliases}
    unseen = [r for r in results if r["query"].lower() not in verbatim]
    no_alias = query_results(concepts, [])
    lines.append(f"query -> concept: {sum(r['ok'] for r in results)} of {len(results)} correct (expected concept returned, no hard negative)")
    lines.append(f"  exactly one concept returned: {sum(r['exact'] for r in results)} of {len(results)}")
    lines.append(f"  queries that are not verbatim alias rows: {sum(r['ok'] for r in unseen)} of {len(unseen)} correct")
    lines.append(f"  with the alias file ignored (concept phrases only): {sum(r['ok'] for r in no_alias)} of {len(no_alias)} correct")
    lines += [f"  WRONG: {r['query']!r} expected {r['expected']} got {r['got']}" for r in results if not r["ok"]]

    judgments = load_judgments()
    relevant = sum(sum(v.values()) for v in judgments.values())
    judged = sum(len(v) for v in judgments.values())
    vehicles = sorted({k[:3] for k in judgments})
    lines.append(f"precision at {TOP_K}: {relevant} of {judged} judged results relevant ({len(vehicles)} vehicles x {len(concepts)} concepts, top {TOP_K} each)")
    per_concept = {c.id: [0, 0] for c in concepts}
    for (_, _, _, cid), v in judgments.items():
        per_concept[cid][0] += sum(v.values())
        per_concept[cid][1] += len(v)
    lines += [f"  {cid:<26} {k} of {n}" for cid, (k, n) in per_concept.items()]
    weights = defaultdict(int)
    for r in results:
        weights[r["expected"]] += 1
    num = sum(weights[c] * per_concept[c][0] for c in weights)
    den = sum(weights[c] * per_concept[c][1] for c in weights)
    lines.append(f"  weighted by the {len(results)} evaluation queries: {num} of {den}")

    if db:
        import duckdb

        con = duckdb.connect(db, read_only=True)
        stale = []
        for (make, model, year), concept in ((v, c) for v in vehicles for c in concepts):
            now = top_hits(con, concept, make, model, year)
            if set(now) != set(judgments.get((make, model, year, concept.id), {})):
                stale.append(f"{make} {model} {year} {concept.id}")
        con.close()
        clean = not stale
        lines.append("judged ids equal the current top results: " + ("yes" if clean else "NO -> re-judge: " + "; ".join(stale)))
    return lines, clean and all(r["ok"] for r in results)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", help="baseline DuckDB file (read-only); checks that the judgments cover the current top results")
    args = ap.parse_args(argv)
    lines, ok = report(args.db)
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
