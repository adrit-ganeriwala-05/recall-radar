"""A4: the alias table merges punctuation/spacing variants only, and ingest applies it."""

import csv
import re

import duckdb
import pytest
from conftest import run_ingest

from recall_radar.data import ingest


def _rows():
    with ingest.ALIASES.open() as f:
        return [(r["make"], r["model_from"], r["model_to"]) for r in csv.DictReader(f)]


def _key(model):
    return re.sub(r"[^A-Z0-9]", "", model)


def test_aliases_differ_only_by_punctuation_or_spacing():
    rows = _rows()
    assert rows, "alias table is empty"
    bad = [r for r in rows if _key(r[1]) != _key(r[2]) or r[1] == r[2]]
    assert bad == []


def test_aliases_have_no_conflicts_or_chains():
    rows = _rows()
    froms = [(m, a) for m, a, _ in rows]
    assert len(froms) == len(set(froms))
    assert not {(m, b) for m, _, b in rows} & set(froms)


def test_f150_and_f250_stay_distinct():
    targets = {(m, a): b for m, a, b in _rows()}
    assert targets.get(("FORD", "F150")) == "F-150"
    assert targets.get(("FORD", "F250"), "F-250") == "F-250"
    assert all(_key(b) != "F250" for (m, a), b in targets.items() if _key(a) == "F150")


def test_ingest_applies_alias_table(tmp_path, monkeypatch):
    table = tmp_path / "aliases.csv"
    table.write_text("make,model_from,model_to\nFORD,F-150,F150\n")
    monkeypatch.setattr(ingest, "ALIASES", table)
    con = duckdb.connect(str(run_ingest(tmp_path)), read_only=True)
    assert con.execute("SELECT model FROM complaint_doc WHERE odino='10000021'").fetchone() == ("F150",)
    assert con.execute("SELECT model FROM complaint_doc WHERE odino='10000022'").fetchone() == ("F-250",)
    con.close()


@pytest.mark.real_data
def test_real_alias_table_leaves_no_punctuation_variants():
    con = duckdb.connect("data/recall_radar.duckdb", read_only=True)
    n = con.execute("""SELECT count(*) FROM (SELECT make, regexp_replace(model, '[^A-Z0-9]', '', 'g') k
                       FROM complaint_doc GROUP BY 1, 2 HAVING count(DISTINCT model) > 1)""").fetchone()[0]
    con.close()
    assert n == 0
