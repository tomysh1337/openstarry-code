from __future__ import annotations

from openstarry_code.router_tiers import (
    HIGHEST_TEXT_TIER,
    TEXT_TIERS,
    TIER_TO_ROUTE_CLASS,
    expand_text_tier_mapping,
    normalize_text_tier,
    tier_index,
)
from openstarry_code.squilla_router.controller import (
    compute_difficulty,
    derive_thinking_mode,
    synthetic_one_hot,
)


def test_canonical_router_ladder_has_seven_ordered_roles() -> None:
    assert TEXT_TIERS == ("c0", "c1", "c2", "c3", "c4", "c5", "c6")
    assert HIGHEST_TEXT_TIER == "c6"
    assert [tier_index(tier) for tier in TEXT_TIERS] == list(range(7))


def test_extended_aliases_and_classifier_telemetry_are_normalized() -> None:
    assert normalize_text_tier(" T4 ") == "c4"
    assert normalize_text_tier("t6") == "c6"
    assert TIER_TO_ROUTE_CLASS["c4"] == "R3"
    assert TIER_TO_ROUTE_CLASS["c6"] == "R3"


def test_historical_ladder_expands_from_nearest_configured_expert_role() -> None:
    expanded = expand_text_tier_mapping(
        {
            "c0": {"model": "fast"},
            "c1": {"model": "balanced"},
            "c2": {"model": "strong"},
            "c3": {"model": "coding"},
            "c4": {"model": "reasoning"},
            "image_model": {"model": "vision"},
        }
    )

    assert list(expanded) == [*TEXT_TIERS, "image_model"]
    assert expanded["c5"]["model"] == "reasoning"
    assert expanded["c6"]["model"] == "reasoning"


def test_synthetic_expert_tiers_have_increasing_difficulty_and_deep_thinking() -> None:
    difficulties = []
    for tier in ("c3", "c4", "c5", "c6"):
        probabilities = synthetic_one_hot(tier)
        assert len(probabilities) == len(TEXT_TIERS)
        assert derive_thinking_mode(probabilities) == "T3"
        difficulties.append(compute_difficulty(probabilities))

    assert difficulties == sorted(difficulties)
    assert len(set(difficulties)) == len(difficulties)
