"""Checks on the real database (`make test-real`), written in SQL outside the method code.

They recount what the detector and the evaluation report: complaint counts per group and month,
the alert rule on every stored episode, and the headline family counts of each committed result.
"""

from __future__ import annotations

import os
import random
from datetime import date, timedelta
from pathlib import Path

import pytest

from recall_radar import contracts as C

pytestmark = pytest.mark.real_data
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def cfg():
    from recall_radar.method.config import load_config

    return load_config()


@pytest.fixture(scope="module")
def con(cfg):
    import duckdb

    db = Path(os.environ.get("RR_DATA_DIR", "data")) / "recall_radar.duckdb"
    if not db.exists():
        pytest.skip(f"{db} not found")
    con = duckdb.connect(str(db), read_only=True)
    if not con.execute("SELECT count(*) FROM alert_episode WHERE config_hash = ?", [cfg["config_hash"]]).fetchone()[0]:
        pytest.skip("no episodes for the working config; run make detect")
    yield con
    con.close()


def test_real_scores_and_episodes_are_finite_and_obey_the_alert_rule(con, cfg):
    h, d = cfg["config_hash"], cfg["detector"]
    bad_scores = con.execute(
        "SELECT count(*) FROM detector_score WHERE config_hash = ? AND scored AND (NOT isfinite(score) OR score < 0 OR baseline_lambda < ?)",
        [h, 2 * d["lambda_floor"]],
    ).fetchone()[0]
    assert bad_scores == 0  # every scored month has a finite score and a baseline at or above twice the floor
    n, broken, shares, bad_months, dup_ids = con.execute(
        """SELECT count(*),
                  count(*) FILTER (WHERE NOT isfinite(peak_score) OR window_count < ? OR peak_score < ? OR ratio < ?),
                  count(*) FILTER (WHERE severity_share NOT BETWEEN 0 AND 1 OR described_share NOT BETWEEN 0 AND 1
                                      OR dup_text_share NOT BETWEEN 0 AND 1 OR avail_fallback_share NOT BETWEEN 0 AND 1),
                  count(*) FILTER (WHERE start_month > end_month OR strftime(alert_date, '%Y-%m') <= start_month),
                  count(*) - count(DISTINCT episode_id)
           FROM alert_episode WHERE config_hash = ?""",
        [d["c_min"], d["s_star"], d["min_ratio"], h],
    ).fetchone()
    assert n > 0 and (broken, shares, bad_months, dup_ids) == (0, 0, 0, 0)
    # the alert flag marks exactly the months of the stored episodes
    flagged = con.execute("SELECT count(*) FROM detector_score WHERE config_hash = ? AND alert", [h]).fetchone()[0]
    in_episodes = con.execute(
        "SELECT sum(date_diff('month', strptime(start_month, '%Y-%m'), strptime(end_month, '%Y-%m')) + 1) FROM alert_episode WHERE config_hash = ?",
        [h],
    ).fetchone()[0]
    assert flagged == in_episodes
    # and no alert becomes available before the month after its first crossing month has started
    assert con.execute(
        "SELECT count(*) FROM alert_episode WHERE config_hash = ? AND alert_date <> (strptime(start_month, '%Y-%m') + INTERVAL 1 MONTH)::DATE", [h]
    ).fetchone()[0] == 0  # fmt: skip


def test_real_group_months_equal_a_direct_count_of_distinct_complaints(con, cfg):
    """300 seeded groups: the stored monthly count equals count(DISTINCT odino) of the complaints
    that are not flagged repeats, by the month they became available."""
    groups = con.execute("SELECT group_id, make, model, model_year, comp_system FROM vehicle_group ORDER BY group_id").fetchall()
    rng = random.Random(int(cfg["seed"]))
    for group_id, make, model, year, system in rng.sample(groups, min(300, len(groups))):
        stored = dict(con.execute("SELECT month, n_distinct FROM group_month WHERE group_id = ? AND n_distinct > 0", [group_id]).fetchall())
        direct = dict(
            con.execute(
                """SELECT strftime(avail_date, '%Y-%m'), count(DISTINCT odino) FROM complaint_system
                   WHERE make = ? AND model = ? AND model_year = ? AND comp_system = ? AND NOT dup_text
                     AND strftime(avail_date, '%Y-%m') <= (SELECT max(month) FROM group_month)
                   GROUP BY 1""",
                [make, model, year, system],
            ).fetchall()
        )
        assert stored == direct, group_id


@pytest.mark.parametrize("period", ["development", "held_out"])
def test_real_headline_family_counts_recounted_in_sql(con, cfg, period):
    """Families, eligible families and families with an exact-vehicle alert 60-730 days before the
    opening, straight from A's tables and the episode table, against the committed result."""
    path = ROOT / "exports" / "demo" / f"results_{period}.json"
    if not path.is_file():
        pytest.skip(f"{path.name} is not committed")
    summary = C.EvaluationSummary.model_validate_json(path.read_text())
    if summary.provenance.config_hash != cfg["config_hash"]:
        pytest.skip("the committed result belongs to another config")
    first, last = (date.fromisoformat(str(x)) for x in cfg["periods"][period])
    after = date.fromisoformat(str(cfg["periods"]["baseline_only"][1])) + timedelta(days=1)
    lo, hi = cfg["evaluation"]["early_window_days"]
    got = con.execute(
        """
        WITH fam AS (SELECT * FROM inv_family WHERE odate_min BETWEEN ? AND ?),
        own AS (SELECT DISTINCT f.family_id, v.model_year FROM fam f JOIN inv_vehicle v
                ON list_contains(f.action_nos, v.action_no) AND v.make = f.make AND v.model = f.model AND v.comp_system = f.comp_system),
        elig AS (SELECT * FROM fam WHERE list_contains(?, first_type) AND year_min IS NOT NULL AND year_max IS NOT NULL
                 AND NOT list_contains(?, comp_system) AND family_id IN (SELECT family_id FROM own)),
        hit AS (SELECT DISTINCT e.family_id FROM elig e JOIN own o USING (family_id)
                JOIN alert_episode a ON a.make = e.make AND a.model = e.model AND a.comp_system = e.comp_system AND a.model_year = o.model_year
                WHERE a.config_hash = ? AND a.alert_date > ? AND date_diff('day', a.alert_date, e.odate_min) BETWEEN ? AND ?)
        SELECT (SELECT count(*) FROM fam), (SELECT count(*) FROM elig), (SELECT count(*) FROM hit)
        """,
        [first, last, list(cfg["evaluation"]["eligible_first_types"]), list(cfg["filters"]["detection_exclude_comp_system"]),
         cfg["config_hash"], after, lo, hi],
    ).fetchone()  # fmt: skip
    cases = summary.cases
    want = (len(cases), sum(c.eligible for c in cases), sum(c.status == "early" and c.match_tier.value == "1" for c in cases))
    assert got == want
