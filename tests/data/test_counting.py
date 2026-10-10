"""A2: distinct-ODINO counting (expected values hand-counted from the fixture JSON)."""


def _group(con, make, model, year, system):
    return con.execute(
        "SELECT count(DISTINCT odino) FROM complaint_system WHERE make=? AND model=? AND model_year=? AND comp_system=?",
        [make, model, year, system],
    ).fetchone()[0]


def test_one_odino_three_rows_two_systems(con):
    # 10000001: STEERING x2 rows + SERVICE BRAKES x1 row -> once per system, once per vehicle
    rows = con.execute("SELECT comp_system FROM complaint_system WHERE odino='10000001' ORDER BY 1").fetchall()
    assert rows == [("SERVICE BRAKES",), ("STEERING",)]
    assert _group(con, "EXAMPLE MOTORS", "ROADSTER", 2017, "STEERING") == 1
    assert _group(con, "EXAMPLE MOTORS", "ROADSTER", 2017, "SERVICE BRAKES") == 1
    assert con.execute("SELECT count(*) FROM complaint_doc WHERE odino='10000001'").fetchone()[0] == 1


def test_vehicle_totals_count_distinct_complaints(con):
    # ROADSTER 2017 docs: 01 02 03 06 07 08 10 11 12 13 14 24 25 26 27 28 29 30 31 = 19
    n = con.execute("SELECT count(*) FROM complaint_doc WHERE make='EXAMPLE MOTORS' AND model='ROADSTER' "
                    "AND model_year=2017").fetchone()[0]
    assert n == 19
    # make/model totals include the two null-year complaints (04, 05)
    n = con.execute("SELECT count(*) FROM complaint_doc WHERE make='EXAMPLE MOTORS' AND model='ROADSTER'").fetchone()[0]
    assert n == 21
    # ELECTRICAL SYSTEM group: base rows 07 08 10 11 12 13 14 27 28 29 30 31 = 12
    assert _group(con, "EXAMPLE MOTORS", "ROADSTER", 2017, "ELECTRICAL SYSTEM") == 12


def test_cross_vehicle_isolation_f150_not_f250(con):
    assert _group(con, "FORD", "F-150", 2017, "ELECTRICAL SYSTEM") == 1
    assert _group(con, "FORD", "F-250", 2017, "ELECTRICAL SYSTEM") == 1
    assert _group(con, "EXAMPLE MOTORS", "F-150", 2017, "ELECTRICAL SYSTEM") == 0


def test_complaint_system_key_is_unique(con):
    dupes = con.execute("SELECT odino, comp_system FROM complaint_system GROUP BY ALL HAVING count(*) > 1").fetchall()
    assert dupes == []


def test_dup_text_flags_repeat_within_window_only(con):
    rows = dict(con.execute("SELECT odino, dup_text FROM complaint_system WHERE comp_system='POWER TRAIN'").fetchall())
    assert rows == {"10000024": False, "10000025": True, "10000026": False}


def test_severe_and_described_flags(con):
    flags = dict(con.execute("SELECT odino, (severe, described) FROM complaint_system").fetchall())
    assert flags["10000028"] == (True, True)
    assert flags["10000029"] == (True, True)
    assert flags["10000031"] == (False, False)
    assert flags["10000030"] == (False, True)
