"""F7 (PRD_v2 §4): text and phrase search over reviewed concepts. Expected values are written by hand."""

from __future__ import annotations

import csv
from pathlib import Path

import duckdb
import pytest

from recall_radar.b_v2 import symptom_eval as E
from recall_radar.b_v2 import symptom_index as SI

ROOT = Path(__file__).resolve().parents[2]
BRAKES, STEERING, LATCHES, ENGINE = ["SERVICE BRAKES"], ["STEERING"], ["LATCHES/LOCKS/LINKAGES"], ["ENGINE"]


@pytest.fixture(scope="module")
def concepts():
    return SI.load_concepts()


@pytest.fixture(scope="module")
def aliases(concepts):
    return SI.load_aliases(concepts=concepts)


# ----------------------------------------------------------------------------- text rules


@pytest.mark.parametrize(
    ("word", "want"),
    [
        ("brakes", "brak"), ("brake", "brak"), ("braking", "brak"),
        ("noise", "nois"), ("noises", "nois"),
        ("stopped", "stop"), ("stopping", "stop"), ("stop", "stop"),  # doubled consonant is undone
        ("shutting", "shut"), ("stalling", "stall"), ("stalled", "stall"),  # "ll" is kept
        ("locks", "lock"), ("locked", "lock"), ("locking", "lock"),
        ("press", "press"),  # "ss" is not a plural
        ("dies", "die"), ("die", "die"),  # short words are left alone
        ("steering", "steer"), ("driving", "driv"), ("drive", "driv"),
    ],
)  # fmt: skip
def test_stem(word, want):
    assert SI.stem(word) == want


def test_tokens_normalise_case_punctuation_negation_and_stopwords():
    assert SI.tokens("My door DOESN'T lock, properly!") == ["door", "not", "lock", "properly"]
    assert SI.tokens("The brakes will not stop the car.") == ["brak", "not", "stop"]
    assert SI.tokens("won’t start") == ["not", "start"]  # typographic apostrophe
    assert SI.tokens("no brakes") == ["no", "brak"]  # "no" is not a stopword
    assert SI.tokens("the a of") == []


def test_phrase_needs_order_and_allows_two_words_between():
    doc = SI.tokens("the door does not always fully lock at night")  # door not always fully lock night
    assert SI.phrase_in(doc, SI.tokens("not lock"))  # two tokens between
    assert not SI.phrase_in(SI.tokens("door not really always fully lock"), SI.tokens("not lock"))  # three between
    assert not SI.phrase_in(doc, SI.tokens("lock not"))  # order matters
    assert not SI.phrase_in(doc, [])


# ----------------------------------------------------------------------------- review files


def test_alias_file_is_reviewed_and_covers_the_prd_examples(concepts, aliases):
    with open(ROOT / "review" / "symptom_aliases.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 40 and all(r["reviewer"] == "B" for r in rows)  # PRD F7.1
    by_phrase = {a.phrase: a.concept_id for a in aliases}
    assert by_phrase["door doesn't lock properly"] == "door_wont_lock"
    assert by_phrase["brakes make noise"] == "brake_noise"
    assert by_phrase["steering wheel shakes"] == "steering_vibration"
    assert by_phrase["engine stalls while driving"] == "stall_while_driving"
    assert {a.concept_id for a in aliases} == {c.id for c in concepts}  # every concept has everyday phrases


@pytest.mark.parametrize(
    ("query", "concept"),
    [
        ("door doesn't lock properly", "door_wont_lock"),
        ("brakes make noise", "brake_noise"),
        ("steering wheel shakes", "steering_vibration"),
        ("engine stalls while driving", "stall_while_driving"),
        # the same symptoms in other words, none of them an alias row
        ("My brakes are making a loud grinding noise!", "brake_noise"),
        ("the steering wheel is shaking badly", "steering_vibration"),
        ("rear door will not lock anymore", "door_wont_lock"),
        ("Engine stalled on the freeway", "stall_while_driving"),
        ("the car won't stop", "brake_failure"),  # alias: no brake word in the query
        ("death wobble", "steering_vibration"),  # alias: no steering word
    ],
)
def test_queries_map_to_exactly_one_concept(concepts, aliases, query, concept):
    assert SI.concepts_for_query(query, concepts, aliases) == [concept]


# PRD F7.2: pairs that must never merge. Each side's wording must not reach the other concept.
PAIRS = [
    ("brake_noise", "brakes squeal every morning", "brake_failure", "brake pedal went to the floor and the car did not stop", BRAKES),
    ("steering_vibration", "steering wheel vibrates at 60 mph", "power_steering_loss", "lost power steering and the wheel was hard to turn", STEERING),
    ("door_wont_lock", "the driver door will not lock with the key fob", "door_opens_while_driving", "rear door flew open while driving", LATCHES),
    ("stall_while_driving", "engine shut off while driving on the highway", "wont_start", "engine cranks but will not start in the morning", ENGINE),
]


@pytest.mark.parametrize(("left", "left_text", "right", "right_text", "systems"), PAIRS)
def test_distinct_concepts_do_not_merge(concepts, aliases, left, left_text, right, right_text, systems):
    by_id = {c.id: c for c in concepts}
    # as queries
    assert SI.concepts_for_query(left_text, concepts, aliases) == [left]
    assert SI.concepts_for_query(right_text, concepts, aliases) == [right]
    # as complaint texts filed under the same component system
    assert by_id[left].doc_matches(SI.tokens(left_text), systems) and not by_id[right].doc_matches(SI.tokens(left_text), systems)
    assert by_id[right].doc_matches(SI.tokens(right_text), systems) and not by_id[left].doc_matches(SI.tokens(right_text), systems)


def test_a_concept_needs_its_component_system_as_well_as_its_words(concepts):
    noise = {c.id: c for c in concepts}["brake_noise"]
    text = SI.tokens("THE BRAKES MAKE A GRINDING NOISE")
    assert noise.doc_matches(text, ["SERVICE BRAKES"]) and noise.doc_matches(text, ["ENGINE", "SERVICE BRAKES, HYDRAULIC"])
    assert not noise.doc_matches(text, ["ENGINE"])  # same words, filed under another system
    assert not noise.doc_matches(SI.tokens("THE ENGINE MAKES A GRINDING NOISE"), ["SERVICE BRAKES"])  # system alone is not enough


def test_committed_evaluation_set_passes(concepts, aliases):
    results = E.query_results(concepts, aliases)
    assert len(results) == 30 and all(r["ok"] for r in results), [r for r in results if not r["ok"]]
    judgments = E.load_judgments()
    assert len({k[:3] for k in judgments}) == 3  # three vehicles (PRD F7.3)
    assert all(len(v) <= E.TOP_K for v in judgments.values())


# ----------------------------------------------------------------------------- search

DOCS = [  # newest first, as the index endpoint serves them
    ("Brakes squeal loudly when stopping.", BRAKES),
    ("Brake pedal went to the floor, the car would not stop.", BRAKES),
    ("Engine makes a squealing noise near the brakes.", ENGINE),
    ("Grinding noise from the rear brakes since last week.", ["SERVICE BRAKES, HYDRAULIC"]),
    ("The radio display flickers on cold mornings.", ["ELECTRICAL SYSTEM"]),
]


def test_search_returns_only_the_concepts_documents_in_the_given_order(concepts, aliases):
    hits = SI.search("brakes make noise", DOCS, concepts, aliases)
    assert [(h.doc_index, h.concept_ids) for h in hits] == [(0, ("brake_noise",)), (3, ("brake_noise",))]
    assert "squeal" in hits[0].matched_terms and "grind" in hits[1].matched_terms
    assert [h.doc_index for h in SI.search("no brakes", DOCS, concepts, aliases)] == [1]


def test_query_without_a_concept_falls_back_to_all_words_present(concepts, aliases):
    hits = SI.search("radio flickering", DOCS, concepts, aliases)
    assert [(h.doc_index, h.concept_ids) for h in hits] == [(4, ())]
    assert SI.search("sunroof leaks", DOCS, concepts, aliases) == []  # the UI then shows the "no similar complaints" line
    assert SI.search("   ", DOCS, concepts, aliases) == [] and SI.search("the of", DOCS, concepts, aliases) == []


def test_search_sees_only_the_documents_it_is_given(concepts, aliases):
    # vehicle isolation is the caller's list: nothing is fetched or remembered between calls
    assert SI.search("brakes make noise", DOCS[4:], concepts, aliases) == []
    assert [h.doc_index for h in SI.search("brakes make noise", DOCS[:1], concepts, aliases)] == [0]


def test_tables_are_a_copy_of_the_review_files(tmp_path, concepts, aliases):
    out = tmp_path / "b_v2_tables.duckdb"
    assert SI.write_tables(out, concepts, aliases) == (len(concepts), len(aliases))
    assert SI.write_tables(out, concepts, aliases) == (len(concepts), len(aliases))  # rerun replaces, never appends
    con = duckdb.connect(str(out), read_only=True)
    row = con.execute("SELECT label, comp_systems, require_all, exclude FROM symptom_concept WHERE id = 'brake_noise'").fetchone()
    assert row[0] == "Brake noise" and "SERVICE BRAKES, HYDRAULIC" in row[1] and len(row[2]) == 2 and row[3] == []
    assert con.execute("SELECT concepts FROM symptom_alias WHERE phrase = 'brakes make noise'").fetchone()[0] == ["brake_noise"]
    assert con.execute("SELECT count(*) FROM symptom_alias").fetchone()[0] >= 40
    con.close()


# ----------------------------------------------------------------------------- isolation (PRD F7.8)


def test_frozen_pipeline_and_replay_never_touch_the_symptom_index():
    for path in sorted((ROOT / "recall_radar" / "method").glob("*.py")):
        source = path.read_text().lower()
        assert "symptom" not in source and "b_v2" not in source, path.name
    for name in ("symptom_index.py", "symptom_eval.py"):
        assert "recall_radar.method" not in (ROOT / "recall_radar" / "b_v2" / name).read_text()
    assert SI.METHOD_LABEL == "Text and phrase search in the current cached snapshot. A match is not a diagnosis."


def test_no_model_or_embedding_dependency():
    source = (ROOT / "recall_radar" / "b_v2" / "symptom_index.py").read_text()
    for banned in ("genai", "openai", "embedding_model", "sentence_transformers", "requests.", "httpx", "urllib"):
        assert banned not in source


@pytest.mark.real_data
def test_real_judgments_cover_the_current_top_results():
    import os

    db = Path(os.environ.get("RR_DATA_DIR", "data")) / "recall_radar.duckdb"
    if not db.exists():
        pytest.skip(f"{db} not found")
    lines, ok = E.report(str(db))
    assert ok, "\n".join(lines)
