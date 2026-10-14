"""Unit tests for the human-channel bounded multilingual parser (P0, scope_plan.md Sec.2/3)."""

import pytest
from process_guardian.llm.human_channel import (
    LAYA_CONFIDENCE_CEILING,
    BoundedChoice,
    CheckpointQuestion,
    HumanChannelClient,
)


@pytest.mark.parametrize(
    "text",
    ["yes", "Done", "spray done", "ok confirmed", "haan", "ho gaya", "kar diya", "aama", "howdu", "aagide"],
)
def test_affirmative_phrases_parse_as_yes_with_high_confidence(text):
    client = HumanChannelClient()
    signal = client.parse(text, CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.YES
    assert signal.confidence >= 0.6
    assert signal.source == "deterministic"


@pytest.mark.parametrize(
    "text",
    ["no", "not done", "pending", "overdue", "nahi", "nahi hua", "illai", "illa"],
)
def test_negative_phrases_parse_as_no_with_high_confidence(text):
    client = HumanChannelClient()
    signal = client.parse(text, CheckpointQuestion.MOISTURE_SIGNED)
    assert signal.choice == BoundedChoice.NO
    assert signal.confidence >= 0.6


@pytest.mark.parametrize("text", ["", "the machine is running fine today", "banana"])
def test_unrecognized_text_is_unknown_with_low_confidence(text):
    client = HumanChannelClient()
    signal = client.parse(text, CheckpointQuestion.RECIPE_MATCHES)
    assert signal.choice == BoundedChoice.UNKNOWN
    assert signal.confidence < 0.6


@pytest.mark.parametrize("text", ["what's happening on the line", "can we chat about cycle 90", "shall I check later"])
def test_short_affirmative_tokens_do_not_match_as_substrings(text):
    """'ha' must not fire inside 'what'/'chat'/'shall' -- single-word tokens match
    whole words only, not substrings."""
    client = HumanChannelClient()
    signal = client.parse(text, CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.UNKNOWN


def test_negative_phrase_beats_affirmative_substring():
    """'not done' must not match the 'done' affirmative token."""
    client = HumanChannelClient()
    signal = client.parse("not done yet", CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.NO


def test_signal_carries_source_and_raw_text():
    """Trust contract rule 3: every signal names its source and confidence -- no
    laundering a guess into a fact."""
    client = HumanChannelClient()
    signal = client.parse("haan spray kar diya", CheckpointQuestion.SPRAY_DONE)
    assert signal.raw_text == "haan spray kar diya"
    assert signal.source in {"laya", "deterministic"}


def test_laya_disabled_by_default_uses_deterministic():
    client = HumanChannelClient()
    assert client.enable_laya is False
    signal = client.parse("yes", CheckpointQuestion.SPRAY_DONE)
    assert signal.source == "deterministic"


def test_laya_enabled_but_unavailable_falls_back_cleanly(monkeypatch):
    """scope_plan.md Sec.6 rule 5: Laya down/unavailable -> deterministic path runs
    unchanged, never a crash. Forces the failure deterministically (not by relying on
    the `laya` package being absent from the environment -- it may or may not be
    installed; see tests/test_human_channel_laya_integration.py for real-model
    coverage when it is)."""
    monkeypatch.setattr("process_guardian.llm.human_channel._get_laya_agent", lambda: None)
    client = HumanChannelClient(enable_laya=True)
    signal = client.parse("yes", CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.YES
    assert signal.source == "deterministic"


def test_laya_inference_failure_falls_back_cleanly(monkeypatch):
    """An exception mid-inference (OOM, malformed response, a laya internal error)
    must fall through to the deterministic path, never raise."""
    monkeypatch.setattr("process_guardian.llm.human_channel._get_laya_agent", lambda: object())

    class _BoomModule:
        @staticmethod
        def decide(*args, **kwargs):
            raise RuntimeError("simulated laya inference failure")

    monkeypatch.setitem(__import__("sys").modules, "laya", _BoomModule())
    client = HumanChannelClient(enable_laya=True)
    signal = client.parse("yes", CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.YES
    assert signal.source == "deterministic"


# --- Negation regression suite -------------------------------------------------
# Every string below was parsed as an affirmative (YES, 0.9 confidence) by the
# original matcher: it only knew the literal bigram "not done", so any other
# negation left the affirmative token ("done", "ok", "pass") to win. On the spray
# gate that meant an operator saying NO reset the spray interval counter.

@pytest.mark.parametrize(
    "text",
    [
        "haven't done it",
        "have not done it",
        "not ok",
        "not okay",
        "not complete",
        "not completed",
        "not yet done",
        "did not pass",
        "not  done",
        "not	done",
        "not-done",
        "never done",
        "moisture not verified",
        "not yet verified",
    ],
)
def test_negations_never_parse_as_affirmative(text):
    client = HumanChannelClient()
    signal = client.parse(text, CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.NO, f"{text!r} must not clear a gate"
    assert signal.confidence >= 0.6


@pytest.mark.parametrize("text", ["done tomorrow", "will do later", "ok wait", "ok I will check", "about to do it"])
def test_deferrals_are_not_confirmations(text):
    """A promise to do it is not a report that it was done."""
    client = HumanChannelClient()
    signal = client.parse(text, CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.NO


@pytest.mark.parametrize("text", ["no problem, done", "no issues, spray applied", "nothing pending, done"])
def test_affirmative_idioms_are_not_read_as_refusals(text):
    """Rejecting a real yes is an adoption failure, which is the real risk here."""
    client = HumanChannelClient()
    signal = client.parse(text, CheckpointQuestion.SPRAY_DONE)
    assert signal.choice == BoundedChoice.YES


def test_ambiguous_negation_plus_affirmative_is_unknown_not_a_guess():
    """Conflicting signals abstain rather than pick a side (SAFE-03)."""
    client = HumanChannelClient()
    signal = client.parse("cannot confirm, maybe ok", CheckpointQuestion.RECIPE_MATCHES)
    assert signal.choice == BoundedChoice.UNKNOWN


# --- Laya placement ------------------------------------------------------------
# The model is positioned as coverage for phrasings the rule set has never seen,
# not as a second opinion on ones it has. These tests pin that contract.

class _StubLaya:
    """Minimal stand-in for the laya module; records whether it was consulted."""

    def __init__(self, choice="A", confidence=0.95, result=None):
        self.choice, self.confidence, self.result = choice, confidence, result
        self.calls = 0

    def decide(self, *args, **kwargs):
        self.calls += 1
        if self.result is not None:
            return self.result

        class _R:
            values = {"confirmed": {"choice": self.choice}}
            answer_confidence = {"confirmed": self.confidence}
        return _R()


def _install(monkeypatch, stub):
    monkeypatch.setattr("process_guardian.llm.human_channel._get_laya_agent", lambda: object())
    monkeypatch.setitem(__import__("sys").modules, "laya", stub)
    return stub


def test_laya_is_not_consulted_when_the_rules_are_confident(monkeypatch):
    """Zero added latency on the common path, and no chance of overriding a rule."""
    stub = _install(monkeypatch, _StubLaya(choice="B"))  # would say NO if asked
    signal = HumanChannelClient(enable_laya=True).parse("yes", CheckpointQuestion.SPRAY_DONE)
    assert stub.calls == 0
    assert signal.choice == BoundedChoice.YES
    assert signal.source == "deterministic"


def test_laya_resolves_a_phrasing_the_rules_do_not_know(monkeypatch):
    """The one place the model earns its place: UNKNOWN becomes a usable answer."""
    stub = _install(monkeypatch, _StubLaya(choice="B", confidence=0.95))
    signal = HumanChannelClient(enable_laya=True).parse(
        "chhidkav baaki hai", CheckpointQuestion.SPRAY_DONE
    )
    assert stub.calls == 1
    assert signal.choice == BoundedChoice.NO
    assert signal.source == "laya"


def test_laya_confidence_is_capped_below_a_rule_match(monkeypatch):
    """Model evidence is weaker evidence and must never present as strong as a rule."""
    _install(monkeypatch, _StubLaya(choice="A", confidence=0.99))
    signal = HumanChannelClient(enable_laya=True).parse("zzz unparseable zzz", CheckpointQuestion.SPRAY_DONE)
    assert signal.source == "laya"
    assert signal.confidence <= LAYA_CONFIDENCE_CEILING < 0.9


@pytest.mark.parametrize(
    "bad_result",
    [
        "a bare string instead of a result object",
        type("R", (), {"values": {"confirmed": "A"}, "answer_confidence": {"confirmed": 0.9}})(),
        type("R", (), {"values": {"confirmed": {"choice": "A"}}, "answer_confidence": {"confirmed": 1.4}})(),
        type("R", (), {"values": {"confirmed": {"choice": "Z"}}, "answer_confidence": {"confirmed": 0.9}})(),
    ],
)
def test_malformed_laya_result_degrades_instead_of_raising(monkeypatch, bad_result):
    """A result with an unexpected shape used to raise straight through the caller."""
    _install(monkeypatch, _StubLaya(result=bad_result))
    signal = HumanChannelClient(enable_laya=True).parse("zzz unparseable zzz", CheckpointQuestion.SPRAY_DONE)
    assert signal.choice in {BoundedChoice.UNKNOWN, BoundedChoice.YES, BoundedChoice.NO}
    assert 0.0 <= signal.confidence <= 1.0
