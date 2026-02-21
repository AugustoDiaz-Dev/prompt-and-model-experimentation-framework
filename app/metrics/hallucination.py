"""Hallucination rate detection module.

Implements heuristic, rule-based hallucination detection — no LLM or API key needed.

Detection strategies:
1. Numeric inconsistency — claimed numbers not found in the context
2. Negation contradictions — "is" vs "is not" for same subject
3. Unsupported superlatives/absolutes — "always", "never", "guaranteed" without grounding
4. Context coverage — how much of the answer is supported word-for-word by context

These heuristics are lightweight and fast. For production use, combine with
an LLM-graded faithfulness metric (e.g. via the Ragas pipeline in Project 1).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HallucinationFlag:
    rule: str           # Which rule triggered
    severity: str       # "low" | "medium" | "high"
    detail: str         # Human-readable explanation
    span: str | None = None  # Offending text fragment


@dataclass
class HallucinationResult:
    answer: str
    context: str | None
    flags: list[HallucinationFlag] = field(default_factory=list)
    hallucination_rate: float = 0.0       # 0.0 – 1.0 overall estimate
    context_coverage: float | None = None # fraction of answer words found in context


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_ABSOLUTE_TERMS = re.compile(
    r"\b(always|never|guaranteed|impossible|certainly|definitely|all|none|every|no one)\b",
    re.IGNORECASE,
)

_NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)*\b")

_NEGATION_RE = re.compile(r"\b(is not|are not|isn't|aren't|cannot|can't|will not|won't)\b", re.IGNORECASE)
_AFFIRMATION_RE = re.compile(r"\b(is|are|can|will)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class HallucinationDetector:
    """Rule-based hallucination detector — fully offline, zero API calls."""

    def detect(self, answer: str, context: str | None = None) -> HallucinationResult:
        """Run all detection rules and return a HallucinationResult.

        Args:
            answer:  The LLM-generated answer to evaluate.
            context: The source context passages used to generate the answer.
                     When None, context-based rules are skipped.
        """
        flags: list[HallucinationFlag] = []

        flags.extend(self._check_unsupported_absolutes(answer, context))
        flags.extend(self._check_numeric_grounding(answer, context))
        flags.extend(self._check_self_contradiction(answer))

        context_coverage: float | None = None
        if context is not None:
            context_coverage = self._compute_context_coverage(answer, context)
            flags.extend(self._check_low_coverage(context_coverage, answer))

        # Weighted hallucination rate estimate
        severity_weights = {"low": 0.1, "medium": 0.25, "high": 0.5}
        raw = sum(severity_weights.get(f.severity, 0.1) for f in flags)
        hallucination_rate = min(1.0, raw)

        return HallucinationResult(
            answer=answer,
            context=context,
            flags=flags,
            hallucination_rate=round(hallucination_rate, 4),
            context_coverage=round(context_coverage, 4) if context_coverage is not None else None,
        )

    # ------------------------------------------------------------------ #
    #  Rule: unsupported absolutes / superlatives                         #
    # ------------------------------------------------------------------ #

    def _check_unsupported_absolutes(
        self, answer: str, context: str | None
    ) -> list[HallucinationFlag]:
        flags: list[HallucinationFlag] = []
        for match in _ABSOLUTE_TERMS.finditer(answer):
            term = match.group()
            # If the same absolute term also appears in context, it's grounded
            grounded = context and term.lower() in context.lower()
            if not grounded:
                flags.append(HallucinationFlag(
                    rule="unsupported_absolute",
                    severity="medium",
                    detail=f"Absolute term '{term}' used without grounding in context",
                    span=term,
                ))
        return flags

    # ------------------------------------------------------------------ #
    #  Rule: numeric claims not found in context                          #
    # ------------------------------------------------------------------ #

    def _check_numeric_grounding(
        self, answer: str, context: str | None
    ) -> list[HallucinationFlag]:
        if context is None:
            return []

        flags: list[HallucinationFlag] = []
        answer_numbers = set(_NUMBER_PATTERN.findall(answer))
        context_numbers = set(_NUMBER_PATTERN.findall(context))

        ungrounded = answer_numbers - context_numbers
        for num in ungrounded:
            # Short numbers (1, 2, 3) are too common to flag
            if len(num) <= 1:
                continue
            flags.append(HallucinationFlag(
                rule="numeric_not_in_context",
                severity="high",
                detail=f"Number '{num}' appears in answer but not in context",
                span=num,
            ))
        return flags

    # ------------------------------------------------------------------ #
    #  Rule: simple self-contradiction (is X ... is not X)               #
    # ------------------------------------------------------------------ #

    def _check_self_contradiction(self, answer: str) -> list[HallucinationFlag]:
        """Detect sentences where close phrases affirm and negate the same thing."""
        flags: list[HallucinationFlag] = []
        sentences = re.split(r"[.!?]\s+", answer)

        for i, sent_a in enumerate(sentences):
            for sent_b in sentences[i + 1:]:
                words_a = set(sent_a.lower().split())
                words_b = set(sent_b.lower().split())
                overlap = words_a & words_b

                # Only flag if sentences share significant content words
                content_overlap = overlap - {
                    "the", "a", "an", "is", "are", "it", "this", "that",
                    "of", "in", "to", "and", "or", "not",
                }
                if len(content_overlap) < 3:
                    continue

                has_neg_a = bool(_NEGATION_RE.search(sent_a))
                has_neg_b = bool(_NEGATION_RE.search(sent_b))

                if has_neg_a != has_neg_b:  # one negates, one affirms
                    flags.append(HallucinationFlag(
                        rule="self_contradiction",
                        severity="high",
                        detail=f"Possible contradiction between sentences with shared topic: {content_overlap}",
                        span=None,
                    ))
                    break  # one flag per sentence pair is enough

        return flags

    # ------------------------------------------------------------------ #
    #  Metric: context word coverage                                      #
    # ------------------------------------------------------------------ #

    def _compute_context_coverage(self, answer: str, context: str) -> float:
        """Fraction of non-trivial answer words that appear in the context."""
        stop_words = {
            "the", "a", "an", "is", "are", "it", "this", "that", "of",
            "in", "to", "and", "or", "not", "was", "be", "by", "for",
            "with", "as", "at", "from", "on", "i", "we", "they", "he", "she",
        }
        answer_words = [w.lower().strip(".,!?;:\"'()[]") for w in answer.split()]
        content_words = [w for w in answer_words if w and w not in stop_words and len(w) > 2]

        if not content_words:
            return 1.0

        context_lower = context.lower()
        covered = sum(1 for w in content_words if w in context_lower)
        return covered / len(content_words)

    def _check_low_coverage(self, coverage: float, answer: str) -> list[HallucinationFlag]:
        if coverage < 0.4:
            return [HallucinationFlag(
                rule="low_context_coverage",
                severity="high",
                detail=f"Only {coverage:.0%} of answer content words found in context — likely hallucinated",
                span=None,
            )]
        if coverage < 0.6:
            return [HallucinationFlag(
                rule="low_context_coverage",
                severity="medium",
                detail=f"{coverage:.0%} context coverage — some claims may be unsupported",
                span=None,
            )]
        return []
