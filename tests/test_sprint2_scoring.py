"""Scoring should be explainable without substring false positives."""
from app.core import rank


def test_full_token_matching_never_claims_unrelated_substrings():
    score, reason = rank("souths", "Mouths researcher", "", "", "")
    assert score == 28
    assert "No direct term match" in reason


def test_short_ai_token_counts_when_present():
    score, reason = rank("AI", "AI founder", "", "", "")
    assert score >= 45
    assert "ai" in reason


def test_matches_do_not_depend_on_unverified_token_order():
    a = rank("robotics developer", "Developer", "Building robotics", "", "")
    b = rank("developer robotics", "Developer", "Building robotics", "", "")
    assert a == b


def test_existing_relevance_examples_remain_relevant():
    score, reason = rank("Embodied AI robotics",
                         "Robotics ML engineer",
                         "Builds embodied AI simulations",
                         "Writes about reinforcement learning", "")
    assert score >= 45
    assert "robotics" in reason
