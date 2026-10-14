"""Human-channel evidence: bounded multilingual operator attestations (P0, scope_plan.md Sec.2/3).

Three shop-floor checkpoints need a yes/no confirmation from an operator, not free-
form chat: spray done this interval? resin lot dried & signed? setpoint matches
recipe R-12? `HumanChannelClient.parse()` maps bounded text (English or common
Hindi/Tamil/Kannada phrasing, transliterated) to a typed `HumanChannelSignal`.

Division of labour: the deterministic matcher below always runs first and its
confident verdict is final. A local Laya backend (convaiinnovations/laya,
multilingual checkpoint, ~644MB, Apache-2.0, opt-in via
PROCESS_GUARDIAN_LAYA_ENABLED=1) is consulted in exactly one situation -- when the
rules return UNKNOWN because the operator used a phrasing they have never seen.
That is the rules' only real failure mode, and it is the model's only real
strength, so it is the only place the model is allowed to speak. It can turn "no
answer" into a candidate answer; it can never turn one answer into a different
one. Model-derived reads are capped at LAYA_CONFIDENCE_CEILING (below an exact
rule match) and carry source="laya" so the engine, the UI and the audit trail all
show where the interpretation came from. Consequences: zero added latency on the
common path, and a wrong model read can at worst request a physical check that was
not needed -- it can never clear a gate the rules would have failed. Any import,
download or inference error falls straight through to the deterministic path and is
never surfaced as a crash (scope_plan.md Sec.6 rule 5: the loop never *depends* on
the model).

Measured against the real convaiinnovations/laya multilingual checkpoint (not a
guess -- this was run end to end): the `noul` (bounded true/false) question type
returned "False" on every one of 13 trivial test inputs including the bare word
"yes", a documented vendor bug (laya GitHub #156: noul can follow its option labels
instead of the input). Their documented workaround -- a 2-option `choice` question
with neutral keys -- fixed the systematic bug but only reached 5/8 (62.5%) on inputs
this product's deterministic parser gets 100% on, including still getting the bare
word "yes" wrong. The vendor's own model card states why: "Base checkpoints are near
chance on typed-decisions zero-shot... Laya is a fast base to specialise, not a
zero-shot decision engine" -- fine-tuning is the documented production path, and is
explicitly out of scope for this build (scope_plan.md Sec.3). The confidence gate
also does not help here: it stayed at "passed" (99.85%) on input with no relation to
the question at all. Laya below is real, working inference, not a stub -- but the
deterministic path is what this product's correctness claims rest on, and that
should not change until a fine-tuned checkpoint is measured, not assumed.
"""

from __future__ import annotations

import math
import os
import re
import threading
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field

CONFIDENCE_THRESHOLD: float = 0.6
# A model-derived read can clear the action threshold (it has to be useful) but can
# never present as strongly as an exact rule match (0.9).
LAYA_CONFIDENCE_CEILING: float = 0.75


class BoundedChoice(str, Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class CheckpointQuestion(str, Enum):
    SPRAY_DONE = "spray_done"
    MOISTURE_SIGNED = "moisture_signed"
    RECIPE_MATCHES = "recipe_matches"


class HumanChannelSignal(BaseModel):
    """Every human-channel signal carries its source and confidence (scope_plan.md
    Sec.6 rule 3) -- never laundering a guess into a fact."""

    question: CheckpointQuestion
    choice: BoundedChoice
    confidence: float = Field(ge=0.0, le=1.0)
    source: str  # "deterministic_fallback" or "laya"
    raw_text: str


# Deliberately small and literal per scope_plan.md Sec.3 ("tight schema, <20 options
# for the demo; fine-tune is the production path, not now"). Longest phrase first so
# "not done" is checked before "done" below. The "not <state>" phrases cover the
# negations of each of the 3 locked questions' own state words (done, confirmed,
# verified, signed, dried, matching) -- still a bounded, literal list, not generic
# negation detection.
_NEGATIVE_PHRASES = sorted(
    {
        # Negations of this product's own three question state-words. Still a
        # bounded literal list, not generic negation detection -- but it now
        # covers every affirmative token below, so no affirmative can survive
        # its own negation (see _deterministic_parse step 1).
        "not done", "not confirmed", "not verified", "not signed", "not dried",
        "not matching", "not match", "not ok", "not okay", "not complete",
        "not completed", "not pass", "not passed", "not yet",
        "nahi hua", "nahi kiya", "nahin hua",
        "no", "nope", "pending", "fail", "failed", "incomplete", "overdue",
        "nahi", "nahin", "illai", "aagala", "illa", "aagilla",
    },
    key=len,
    reverse=True,
)
_AFFIRMATIVE_PHRASES = sorted(
    {
        "ho gaya", "kar diya", "haan ji",
        "yes", "yeah", "yep", "done", "confirmed", "ok", "okay",
        "pass", "passed", "complete", "completed",
        "applied", "sprayed", "signed", "verified", "dried", "checked", "cleared",
        "haan", "ha", "hogaya", "kiya",
        "aama", "seydhachu", "mudinthathu",
        "howdu", "aagide", "maadidini",
    },
    key=len,
    reverse=True,
)
# A promise to do it is not a confirmation that it was done. Without these,
# "spray done tomorrow" reads as an affirmative and clears the interval gate.
_DEFERRAL_PHRASES = sorted(
    {"tomorrow", "later", "next shift", "will do", "will check", "wait", "going to", "about to", "baad mein", "nantar"},
    key=len,
    reverse=True,
)
# Idioms where a negative word is actually part of an affirmative report. Checked
# before the negative list so "no problem, done" is not read as a refusal -- the
# adoption cost of rejecting a real yes is what keeps operators from using the gate.
_AFFIRMATIVE_IDIOMS = ("no problem", "no issue", "no issues", "nothing pending", "no delay")
# Tokens that negate a following affirmative even when the exact bigram is unlisted.
_NEGATOR_TOKENS = {
    "not", "never", "no", "dont", "didnt", "havent", "hasnt", "isnt",
    "wasnt", "cant", "cannot", "couldnt", "wont", "nahi", "nahin", "illa", "illai",
}
# Single-word affirmatives, used to tell a governed negation ("never done") from a
# genuinely conflicted statement ("cannot confirm, maybe ok").
_AFFIRMATIVE_SINGLE = {p for p in _AFFIRMATIVE_PHRASES if " " not in p}
# An operator asking a question has not attested to anything.
_INTERROGATIVE_OPENERS = {"shall", "should", "can", "could", "do", "did", "is", "are", "what", "when", "why", "how"}


# A 2-option `choice` question per locked P0 question (scope_plan.md Sec.3), per
# convaiinnovations/laya's own documented workaround for noul's label-bias bug
# (README "Honest Limits", laya GitHub #156): neutral keys, yes/no wording in the
# criteria text, not in the key itself.
def _confirmation_question(instructions: str) -> Dict[str, Any]:
    return {
        "type": "choice",
        "instructions": instructions,
        "criteria": {
            "A": "yes, confirmed",
            "B": "no, not confirmed",
        },
    }


_QUESTIONS_BY_CHECKPOINT: Dict[CheckpointQuestion, Dict[str, Any]] = {
    CheckpointQuestion.SPRAY_DONE: _confirmation_question(
        "Has the mold-release spray been applied this interval?"
    ),
    CheckpointQuestion.MOISTURE_SIGNED: _confirmation_question(
        "Has the resin lot been dried and signed off by QC?"
    ),
    CheckpointQuestion.RECIPE_MATCHES: _confirmation_question(
        "Does the active machine setpoint match the signed recipe R-12?"
    ),
}

# Loading the multilingual checkpoint is expensive (network fetch + model init), so
# one process-wide agent is loaded once and reused -- never per call, never per
# HumanChannelClient instance. A failed load is cached too, so a missing/broken
# install doesn't retry a slow failure on every single attestation.
_laya_agent: Any = None
_laya_load_failed: bool = False
_laya_lock = threading.Lock()


def _get_laya_agent() -> Optional[Any]:
    global _laya_agent, _laya_load_failed
    if _laya_agent is not None:
        return _laya_agent
    if _laya_load_failed:
        return None
    with _laya_lock:
        if _laya_agent is not None:
            return _laya_agent
        if _laya_load_failed:
            return None
        try:
            import laya
            _laya_agent = laya.load("ml")
        except Exception:
            _laya_load_failed = True
            return None
    return _laya_agent


def _normalize(text: str) -> str:
    """Fold the spelling variants that used to let a negation slip through.

    "haven't done it", "not-done" and "not  done" all have to reach the same
    literal "not done" the phrase list knows about, or the affirmative "done"
    wins and a refusal is recorded as a confirmation.
    """
    s = text.strip().lower()
    s = s.replace("’", "'")           # curly apostrophe
    s = re.sub(r"n't\b", " not", s)        # haven't -> have not
    s = re.sub(r"[-_/]+", " ", s)          # not-done -> not done
    s = re.sub(r"\s+", " ", s)             # collapse runs of whitespace/tabs
    return s


def _deterministic_parse(text: str) -> Tuple[BoundedChoice, float]:
    normalized = _normalize(text)
    if not normalized:
        return BoundedChoice.UNKNOWN, 0.0

    # Single-word tokens are matched as whole words, not substrings: "ha" must not
    # fire on "what" or "chat", and "no" must not fire on "nobody".
    seq = re.findall(r"[a-z']+", normalized)
    tokens = set(seq)

    def _matches(phrase: str) -> bool:
        return phrase in tokens if " " not in phrase else phrase in normalized

    # 0. A question is not an attestation. "shall I check later" reports nothing,
    #    so it must not register as either a confirmation or a refusal.
    is_opener = bool(seq) and seq[0] in _INTERROGATIVE_OPENERS and not (tokens & _NEGATOR_TOKENS)
    if normalized.endswith("?") or is_opener:
        return BoundedChoice.UNKNOWN, 0.3

    idiom_hit = any(idiom in normalized for idiom in _AFFIRMATIVE_IDIOMS)
    has_affirmative = any(_matches(p) for p in _AFFIRMATIVE_PHRASES)

    # 1. An explicit negative phrase is decisive ("not done", "nahi hua", bare "no"),
    #    unless the only negative word is part of an affirmative idiom.
    if not idiom_hit:
        for phrase in _NEGATIVE_PHRASES:
            if _matches(phrase):
                return BoundedChoice.NO, 0.9

    # 2. A promise to do it later is not a confirmation.
    for phrase in _DEFERRAL_PHRASES:
        if _matches(phrase):
            return BoundedChoice.NO, 0.9

    # 3. A negator token with no listed phrase is still a negation. If it directly
    #    governs an affirmative ("never done") that is a refusal; if the two are far
    #    apart the text is genuinely conflicted ("cannot confirm, maybe ok") and we
    #    abstain and re-ask rather than guess a side (SAFE-03).
    if not idiom_hit and tokens & _NEGATOR_TOKENS:
        neg_idx = [i for i, t in enumerate(seq) if t in _NEGATOR_TOKENS]
        aff_idx = [i for i, t in enumerate(seq) if t in _AFFIRMATIVE_SINGLE]
        governs = any(0 < (a - n) <= 2 for n in neg_idx for a in aff_idx)
        if governs or not has_affirmative:
            return BoundedChoice.NO, 0.9
        return BoundedChoice.UNKNOWN, 0.4

    if has_affirmative:
        return BoundedChoice.YES, 0.9

    return BoundedChoice.UNKNOWN, 0.3


class HumanChannelClient:
    """Thin client over a bounded typed-decision model for shop-floor attestations."""

    def __init__(self, enable_laya: Optional[bool] = None):
        self.enable_laya = (
            enable_laya
            if enable_laya is not None
            else os.environ.get("PROCESS_GUARDIAN_LAYA_ENABLED", "0") == "1"
        )

    def parse(self, text: str, question: CheckpointQuestion) -> HumanChannelSignal:
        """Deterministic rules decide; the model only speaks where they are blind.

        The rule set is exact on every phrasing it knows, and that is the common
        case, so it runs first and its confident verdict is final -- the model is
        never consulted and adds no latency there. Its real failure mode is an
        *unseen* phrasing (most often a local-language one), which it reports as
        UNKNOWN. That is the only place a 322M multilingual model earns its keep:
        it turns "no answer" into a candidate answer, never a confident answer
        into a different one. Model-derived reads are capped below the rules'
        confidence and labelled source="laya", so the engine and the audit trail
        both show where the interpretation came from (scope_plan.md Sec.6 rules 1-3).
        """
        choice, confidence = _deterministic_parse(text)

        if choice is BoundedChoice.UNKNOWN and self.enable_laya:
            laya_result = self._try_laya_parse(text, question)
            if laya_result is not None:
                laya_choice, laya_confidence = laya_result
                if laya_choice is not BoundedChoice.UNKNOWN:
                    return HumanChannelSignal(
                        question=question,
                        choice=laya_choice,
                        # Weaker evidence than a rule match, and it must stay that
                        # way: measured base-checkpoint accuracy on molding text is
                        # well short of the rules (see module docstring).
                        confidence=min(laya_confidence, LAYA_CONFIDENCE_CEILING),
                        source="laya",
                        raw_text=text,
                    )

        return HumanChannelSignal(
            question=question, choice=choice, confidence=confidence,
            source="deterministic", raw_text=text,
        )

    def _try_laya_parse(self, text: str, question: CheckpointQuestion) -> Optional[Tuple[BoundedChoice, float]]:
        agent = _get_laya_agent()
        if agent is None:
            return None
        # Everything that touches the model result stays inside the try: a result
        # with an unexpected shape (bare string instead of a dict, missing .values,
        # a confidence of NaN or 1.2) must degrade to the deterministic answer, not
        # raise through the caller and take the decision loop down with it
        # (scope_plan.md Sec.6 rule 5).
        try:
            import laya
            questions = {"confirmed": _QUESTIONS_BY_CHECKPOINT[question]}
            result = laya.decide(
                agent, text, questions=questions,
                return_details=True, min_confidence=CONFIDENCE_THRESHOLD,
            )

            answer = result.values.get("confirmed")
            raw_confidence = result.answer_confidence.get("confirmed", 0.0) or 0.0
            confidence = float(raw_confidence)
            if not math.isfinite(confidence):
                return None
            confidence = min(max(confidence, 0.0), 1.0)

            if not isinstance(answer, dict) or answer.get("choice") not in ("A", "B"):
                # Either laya's own min_confidence gate fired, or the shape is not
                # what the schema promised. Unknown, never a guessed side.
                return BoundedChoice.UNKNOWN, confidence

            choice = BoundedChoice.YES if answer["choice"] == "A" else BoundedChoice.NO
            return choice, confidence
        except Exception:
            # Any inference-time failure (OOM, malformed response, a laya internal
            # error) falls through to the deterministic path -- never a crash.
            return None
