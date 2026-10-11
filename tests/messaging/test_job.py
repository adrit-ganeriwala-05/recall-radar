"""PRD v2 F9.6 scheduled job (mocked NHTSA + provider): kill switch, seed-then-diff, daily cadence per vehicle,
quiet-hours digests sent by a later flush run, and STOP honored before an unsolicited send."""

from __future__ import annotations

from recall_radar.messaging import job
from recall_radar.messaging.provider import MockProvider
from recall_radar.messaging.store import connect

from .test_messaging import at, enroll, say, snap


def setup(tmp_path):
    db = tmp_path / "messaging.sqlite"
    con = connect(db)
    enroll(con)
    con.close()
    return db


def counting(complaints, campnos=()):
    calls = []
    def f(mk, md, yr):
        calls.append((mk, md, yr))
        return snap(complaints, campnos)(mk, md, yr)
    f.calls = calls
    return f


def test_disabled_does_nothing(monkeypatch, capsys):
    monkeypatch.setenv("RR_MESSAGING_ENABLED", "0")
    assert job.main() == 0 and "disabled" in capsys.readouterr().out


def test_seed_then_daily_diff_sends_one_alert(tmp_path):
    db, prov = setup(tmp_path), MockProvider()
    first = counting({"1": ["STEERING"]})
    assert job.run_once(db, first, prov, now=at(10)) == (0, 0) and len(first.calls) == 1  # seeded silently
    again = counting({"1": ["STEERING"], "2": ["BRAKES"]}, ["26V001000"])
    assert job.run_once(db, again, prov, now=at(10) + 900) == (0, 0) and again.calls == []  # not due yet
    events, sent = job.run_once(db, again, prov, now=at(10, day=13))
    assert events == 2 and sent == 1 and len(again.calls) == 1
    body = prov.sent[-1][1]
    assert "1 newly published distinct complaints mentioning BRAKES" in body and "26V001000" in body


def test_quiet_hours_hold_the_alert_until_a_later_flush(tmp_path):
    db, prov = setup(tmp_path), MockProvider()
    job.run_once(db, counting({"1": ["STEERING"]}), prov, now=at(22, day=11))
    events, sent = job.run_once(db, counting({"1": ["STEERING"], "2": ["BRAKES"]}), prov, now=at(22, day=12))
    assert events == 1 and sent == 0  # 22:00 local: queued, not sent
    assert job.run_once(db, counting({}), prov, now=at(8, day=13) + 60) == (0, 1)  # flush after 08:00, no refetch


def test_stop_before_the_flush_cancels_the_alert(tmp_path):
    db, prov = setup(tmp_path), MockProvider()
    job.run_once(db, counting({"1": ["STEERING"]}), prov, now=at(22, day=11))
    job.run_once(db, counting({"1": ["STEERING"], "2": ["BRAKES"]}), prov, now=at(22, day=12))
    con = connect(db)
    say(con, "STOP", "stop-1", prov=prov)
    con.close()
    n = len(prov.sent)
    assert job.run_once(db, counting({}), prov, now=at(9, day=13)) == (0, 0) and len(prov.sent) == n


def test_lock_held_means_skip(tmp_path):
    from recall_radar.messaging.store import take_lock
    db = setup(tmp_path)
    con = connect(db)
    assert take_lock(con, "monitor", "someone-else", ttl_s=900)
    con.close()
    assert job.run_once(db, counting({}), MockProvider()) is None
