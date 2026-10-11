"""PRD v2 F9.7 with the Gemini brain (mocked model; no network): the model plans and rewords only, keyword
guards win, and a rewording that changes a number or link, or adds safety/legal wording, is discarded."""

from __future__ import annotations

import pytest

from recall_radar.messaging import brain, conversation
from recall_radar.messaging import templates as T

from .test_messaging import FakeAnalysis


class FakeBrain:
    def __init__(self, plan=None, phrase=None, fail=False):
        self._plan, self._phrase, self.fail, self.phrased = plan, phrase, fail, []

    def plan(self, text, ctx):
        if self.fail:
            raise TimeoutError
        return self._plan

    def phrase(self, question, facts):
        self.phrased.append(facts)
        new = self._phrase(facts) if callable(self._phrase) else self._phrase
        return new if brain.acceptable(new, facts) else None


def test_model_extracts_the_vehicle_from_free_text():
    b = FakeBrain(plan={"intent": "problems", "year": 2017, "make": "Example Motors", "model": "Roadster"})
    r, ctx = conversation.answer("my old example roadster from 17 keeps acting up, do others see this?", None, FakeAnalysis(), brain=b)
    assert "STEERING (20)" in r and ctx["make"] == "EXAMPLE MOTORS"


def test_model_vehicle_not_in_data_is_not_invented():
    b = FakeBrain(plan={"intent": "count", "year": 2031, "make": "Nope", "model": "Car"})
    r, ctx = conversation.answer("how many complaints for my flying car", None, FakeAnalysis(), brain=b)
    assert r.startswith("Which vehicle?") and ctx is None


def test_keyword_guards_win_over_the_model():
    b = FakeBrain(plan={"intent": "problems", "year": 2017, "make": "Example Motors", "model": "Roadster"})
    r, _ = conversation.answer("is my 2017 example motors roadster safe to drive", None, FakeAnalysis(), brain=b)
    assert r == T.NO_DIAGNOSIS
    r, _ = conversation.answer("recalls for VIN 1HGCM82633A004352", None, FakeAnalysis(), brain=b)
    assert r == T.VIN_HANDOFF


def test_claim_and_greeting_get_fixed_texts():
    r, _ = conversation.answer("can you help with my insurance claim", None, FakeAnalysis(), brain=FakeBrain(plan={"intent": "claim_help"}))
    assert r == T.CLAIM_HELP and "can't give insurance or legal advice" in r
    r, _ = conversation.answer("hey who are you", None, FakeAnalysis(), brain=FakeBrain(plan={"intent": "greeting"}))
    assert r == T.SCOPE


def test_good_rewording_is_used_and_bad_ones_are_discarded():
    q = "how many complaints for the 2017 example motors roadster"
    url = T.link(2017, "EXAMPLE MOTORS", "ROADSTER")
    good = f"People filed 35 distinct complaints about the 2017 Example Motors Roadster across 2 groups (data as of 2026-10-10). More: {url}"
    plan = {"intent": "count"}
    r, _ = conversation.answer(q, None, FakeAnalysis(), brain=FakeBrain(plan=plan, phrase=good))
    assert r == good
    for bad in (good.replace("35", "36"),                       # changed number
                good.replace(url, "https://example.com"),       # changed link
                good.replace(f" More: {url}", ""),              # dropped link
                good + " It is safe to drive.",                 # safety claim
                good + " You should sue the dealer."):          # legal advice
        r, _ = conversation.answer(q, None, FakeAnalysis(), brain=FakeBrain(plan=plan, phrase=bad))
        assert "35 distinct NHTSA complaint IDs" in r, bad   # deterministic reply kept


def test_fixed_texts_are_never_reworded_and_model_failure_falls_back():
    b = FakeBrain(plan={"intent": "how_to_report"}, phrase="anything")
    r, _ = conversation.answer("how do i report a problem", None, FakeAnalysis(), brain=b)
    assert r == T.REPORT_HOWTO and b.phrased == []
    r, _ = conversation.answer("how many complaints for the 2017 example motors roadster", None, FakeAnalysis(), brain=FakeBrain(fail=True))
    assert "35 distinct NHTSA complaint IDs" in r


def test_from_env_needs_key_and_model_and_respects_kill_switch(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("RR_GEMINI_MODEL", "m")
    assert brain.from_env() is None
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    assert brain.from_env() is not None
    monkeypatch.setenv("RR_BRAIN", "0")
    assert brain.from_env() is None


def test_gemini_http_failure_is_none(monkeypatch):
    def boom(*a, **k):
        raise OSError("network down")
    monkeypatch.setattr(brain.urllib.request, "urlopen", boom)
    g = brain.Gemini("k", "m")
    assert g.plan("hi", None) is None and g.phrase("q", "facts 1") is None


@pytest.mark.parametrize("intent", brain.INTENTS)
def test_every_planned_intent_gets_a_reply(intent):
    r, _ = conversation.answer("2017 example motors roadster", None, FakeAnalysis(), brain=FakeBrain(plan={"intent": intent}))
    assert r


def test_digits_in_the_model_name_are_grounded():
    class Digits(FakeAnalysis):
        def get(self, path, **p):
            if path == "/api/makes":
                return {"items": ["FORD"]}
            if path == "/api/models":
                return {"items": ["F-150"]}
            return super().get(path, **p)
    r, _ = conversation.answer("how many complaints for the 2017 ford f-150", None, Digits())
    assert "35 distinct NHTSA complaint IDs" in r and "F-150" in r and "couldn't check" not in r
    assert not conversation.numbers_grounded("2017 FORD F-150: 36 complaints", "35 2017 FORD F-150")  # still strict
