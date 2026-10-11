"""F1 (PRD v2): recall cards' official text and flags, built into a new DB file (synthetic_fixture)."""

from __future__ import annotations

import hashlib
import socket
import zipfile

import duckdb
import pytest

from recall_radar.data import recall_v2, snapshot


def rcl(campno, make="EXAMPLE MOTORS", model="ROADSTER", year="2017", comp="STEERING: COLUMN", typ="V",
        rcdate="20190204", summary="The steering <column> bolt may loosen.", conseq="Reduced \\ steering \"control\".",
        remedy="Dealers will tighten the bolt.", dnd="No", park="No"):
    row = [""] * recall_v2.RCL_N_FIELDS
    for name, value in {"CAMPNO": campno, "MAKETXT": make, "MODELTXT": model, "YEARTXT": year, "COMPNAME": comp,
                        "RCLTYPECD": typ, "RCDATE": rcdate, "DESC_DEFECT": summary, "CONEQUENCE_DEFECT": conseq,
                        "CORRECTIVE_ACTION": remedy, "DO_NOT_DRIVE": dnd, "PARK_OUTSIDE": park}.items():
        row[recall_v2.RCL_V2_KEEP[name] - 1] = value
    return row


ROWS = [
    rcl("18V000000", dnd="Yes"),
    rcl("18V000000", dnd="Yes"),                                   # exact repeat -> one card
    rcl("18V000000", comp="STEERING: WHEEL", rcdate="20190110", dnd="Yes"),  # second component, earlier date
    rcl("19V111000", comp="ELECTRICAL SYSTEM", dnd="no", park="YES", conseq=""),  # case; missing consequence
    rcl("20V222000", comp="SERVICE BRAKES", dnd="", park="maybe"),  # unknown flags
    rcl("21V333000", model="SPEEDSTER", comp="STEERING: COLUMN"),  # same component, other model
    rcl("22E444000", typ="E"),                                      # equipment campaign: not a vehicle card
    rcl("23V555000", year="9999"),                                  # unknown model year: no card
]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("rclv2")
    raw = tmp / "raw"
    raw.mkdir()
    with zipfile.ZipFile(raw / recall_v2.RCL_FILE, "w") as zf:
        zf.writestr("FLAT_RCL_POST_2010.txt", "".join("\t".join(r) + "\r\n" for r in ROWS) + "short\tline\r\n")
    lock = raw / "SNAPSHOT.lock.json"
    snapshot.write_lock(snapshot.build_lock(
        raw, (snapshot.Source(recall_v2.RCL_FILE, "https://example.invalid/r.zip", "2026-10-10T00:00:00-04:00"),)), lock)
    base = tmp / "recall_radar.duckdb"
    con = duckdb.connect(str(base))
    con.execute("CREATE TABLE complaint_doc AS SELECT 1 AS odino, 'X' AS descr")
    con.execute("CREATE TABLE eval_metric AS SELECT 'early_coverage_all' AS name, 0.0 AS value")
    con.close()
    before = hashlib.sha256(base.read_bytes()).hexdigest()
    real_socket = socket.socket
    socket.socket = lambda *a, **k: pytest.fail("F1 build must not touch the network")  # type: ignore[assignment]
    try:
        report = recall_v2.run(base, tmp / "recall_radar_v2.duckdb", raw, lock)
    finally:
        socket.socket = real_socket
    return report, base, before, tmp / "recall_radar_v2.duckdb"


def cards(db, make="EXAMPLE MOTORS", model="ROADSTER", year=2017):
    c = duckdb.connect(str(db), read_only=True)
    try:
        cols = [d[0] for d in c.execute("SELECT * FROM recall_campaign_v2 LIMIT 0").description]
        return {r[0]: dict(zip(cols, r, strict=True)) for r in c.execute(
            "SELECT * FROM recall_campaign_v2 WHERE make = ? AND model = ? AND model_year = ? ORDER BY campno",
            [make, model, year]).fetchall()}
    finally:
        c.close()


@pytest.mark.parametrize(("raw", "want"), [
    (True, True), (False, False), ("true", True), ("TRUE", True), ("Yes", True), ("y", True), (" yes ", True),
    ("false", False), ("FALSE", False), ("No", False), ("n", False),
    ("", None), (None, None), ("maybe", None), (0, None), (1, None), ("1", None), ("0", None),
])
def test_flag_normalisation(raw, want):
    assert recall_v2.normalize_flag(raw) is want


def test_one_card_per_campno_for_exactly_the_selected_vehicle(built):
    got = cards(built[3])
    assert sorted(got) == ["18V000000", "19V111000", "20V222000"]  # no 21V (other model), 22E (equipment), 23V (9999)
    c = got["18V000000"]
    assert c["source_rows"] == 3 and c["component"] == "STEERING: COLUMN; STEERING: WHEEL"
    assert str(c["report_date"]) == "2019-01-10" and c["report_date_basis"] == "Report received date (RCDATE)"


def test_no_component_only_match(built):
    # 21V333000 has the same component as the ROADSTER cards but is for SPEEDSTER only
    assert sorted(cards(built[3], model="SPEEDSTER")) == ["21V333000"]
    assert "21V333000" not in cards(built[3])


def test_official_text_is_verbatim_and_missing_fields_are_null(built):
    got = cards(built[3])
    assert got["18V000000"]["summary"] == "The steering <column> bolt may loosen."
    assert got["18V000000"]["consequence"] == 'Reduced \\ steering "control".'
    assert got["19V111000"]["consequence"] is None


def test_flags_in_the_table(built):
    got = cards(built[3])
    assert (got["18V000000"]["park_it"], got["18V000000"]["park_outside"]) == (True, False)
    assert (got["19V111000"]["park_it"], got["19V111000"]["park_outside"]) == (False, True)
    assert (got["20V222000"]["park_it"], got["20V222000"]["park_outside"]) == (None, None)


def test_baseline_untouched_and_protected_tables_identical(built):
    report, base, before, v2 = built
    assert hashlib.sha256(base.read_bytes()).hexdigest() == before
    assert report["protected_identical"] and report["protected_tables"] == 2
    assert report["new_tables"] == ["recall_campaign_v2"]
    assert report["rcl_rows_read"] == len(ROWS) + 1 and report["rcl_rows_rejected"] == 1


def test_refuses_to_write_the_baseline(built, tmp_path):
    _, base, _, _ = built
    with pytest.raises(SystemExit, match="new file"):
        recall_v2.run(base, base, tmp_path, tmp_path / "lock.json")
