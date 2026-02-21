import pytest
from app.metrics.hallucination import HallucinationDetector

def test_unsupported_absolutes():
    detector = HallucinationDetector()
    result = detector.detect("This is definitely the always best solution.", "A potential solution is provided.")
    assert result.hallucination_rate > 0.0
    flags = [f.rule for f in result.flags]
    assert "unsupported_absolute" in flags

def test_numeric_grounding():
    detector = HallucinationDetector()
    result = detector.detect("It costs $1500.", "The price fluctuates.")
    flags = [f.rule for f in result.flags]
    assert "numeric_not_in_context" in flags

def test_self_contradiction():
    detector = HallucinationDetector()
    result = detector.detect("The shiny red car is extremely fast on the track. The shiny red car is not extremely fast on the track.")
    flags = [f.rule for f in result.flags]
    assert "self_contradiction" in flags

def test_low_context_coverage():
    detector = HallucinationDetector()
    result = detector.detect("The sky is blue and beautiful today.", "I love apples.")
    flags = [f.rule for f in result.flags]
    assert "low_context_coverage" in flags
