"""Canonical router tier identifiers, legacy aliases, and the typed tier view."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

TEXT_TIERS: tuple[str, ...] = ("c0", "c1", "c2", "c3", "c4", "c5", "c6")
CLASSIFIER_TEXT_TIERS: tuple[str, ...] = TEXT_TIERS[:4]
DEFAULT_TEXT_TIER = "c1"
HIGHEST_TEXT_TIER = "c6"
IMAGE_TIER = "image_model"

LEGACY_TEXT_TIER_ALIASES: dict[str, str] = {
    "t0": "c0",
    "t1": "c1",
    "t2": "c2",
    "t3": "c3",
    "t4": "c4",
    "t5": "c5",
    "t6": "c6",
}

ROUTE_CLASS_TO_TIER: dict[str, str] = {
    f"R{index}": tier for index, tier in enumerate(CLASSIFIER_TEXT_TIERS)
}
TIER_TO_ROUTE_CLASS: dict[str, str] = {
    **{tier: route for route, tier in ROUTE_CLASS_TO_TIER.items()},
    # The bundled classifier has four output heads. Higher operator-defined
    # roles retain the strongest classifier class in telemetry while the
    # canonical tier id carries the finer seven-level routing decision.
    "c4": "R3",
    "c5": "R3",
    "c6": "R3",
}


def normalize_text_tier(value: object) -> str | None:
    """Return the canonical text tier id for *value*, accepting t0-t6 aliases."""

    if value is None:
        return None
    tier = str(value).strip().lower()
    if not tier:
        return None
    if tier in TEXT_TIERS:
        return tier
    return LEGACY_TEXT_TIER_ALIASES.get(tier)


def normalize_tier_id(value: object) -> str | None:
    """Normalize any known tier id, preserving the image tier."""

    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw == IMAGE_TIER:
        return IMAGE_TIER
    return normalize_text_tier(raw)


def normalize_target_id(value: object) -> str:
    """Normalize router-control target ids such as tier:t3 -> tier:c3."""

    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("tier:"):
        tier = normalize_text_tier(raw.removeprefix("tier:"))
        return f"tier:{tier}" if tier else raw
    return raw


def normalize_tier_mapping(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a copy of a tier mapping with legacy text tier keys canonicalized."""

    if not isinstance(mapping, Mapping):
        return {}
    normalized: dict[str, Any] = {}
    for key, value in mapping.items():
        tier = normalize_tier_id(key)
        out_key = tier or str(key)
        if out_key in normalized and str(key).strip().lower() not in TEXT_TIERS:
            continue
        normalized[out_key] = value
    return normalized


def expand_text_tier_mapping(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    """Expand a complete historical c0-c3 ladder through c6 in memory.

    Each missing expert role inherits the nearest configured lower role. Invalid
    existing values are preserved so downstream validation can report them.
    Non-text tiers are kept after the canonical text ladder.
    """

    normalized = normalize_tier_mapping(mapping)
    if not all(isinstance(normalized.get(tier), Mapping) for tier in CLASSIFIER_TEXT_TIERS):
        return normalized

    inherited: Mapping[str, Any] = normalized[CLASSIFIER_TEXT_TIERS[-1]]
    for tier in TEXT_TIERS[len(CLASSIFIER_TEXT_TIERS) :]:
        if tier in normalized:
            current = normalized[tier]
            if isinstance(current, Mapping):
                inherited = current
            continue
        normalized[tier] = dict(inherited)

    ordered = {tier: normalized[tier] for tier in TEXT_TIERS if tier in normalized}
    ordered.update({key: value for key, value in normalized.items() if key not in TEXT_TIERS})
    return ordered


def tier_index(value: object) -> int:
    """Return 0-6 for known text tiers; -1 for unknown values."""

    tier = normalize_text_tier(value)
    if tier is None:
        return -1
    try:
        return TEXT_TIERS.index(tier)
    except ValueError:
        return -1


@dataclass(frozen=True)
class TierConfig:
    """Typed view over one router tier entry.

    Tier entries travel as plain dicts through config/TOML/RPC (and some
    tests pass objects); this is the one place that knows the field names
    and their normalization, so consumers stop re-implementing
    ``.get("model")``-style plumbing with divergent defaults.
    """

    provider: str = ""
    model: str = ""
    description: str = ""
    thinking_level: str | None = None
    supports_image: bool = False
    image_only: bool = False

    @classmethod
    def from_value(cls, value: object) -> TierConfig:
        """Build from a tier dict or attribute-style object; tolerant of None."""

        def _get(key: str, default: object = None) -> object:
            if isinstance(value, Mapping):
                return value.get(key, default)
            return getattr(value, key, default)

        thinking = _get("thinking_level")
        return cls(
            provider=str(_get("provider") or "").strip(),
            model=str(_get("model") or "").strip(),
            description=str(_get("description") or ""),
            thinking_level=(str(thinking).strip() if thinking not in (None, "") else None),
            supports_image=bool(_get("supports_image", False)),
            image_only=bool(_get("image_only", False)),
        )
