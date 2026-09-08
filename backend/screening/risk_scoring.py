"""Case-level risk scoring.

The legacy score was simply ``max(match.confidence)``. That overweights a single
broad address match (e.g. "Hong Kong" hitting 128 entities) and underweights
cases where several independent evidence types all point at the same entity.

This module computes a risk score that considers:

- The best evidence tier found (identifier exact > name exact > name fuzzy >
  address fuzzy > 2nd-degree network).
- Match diversity on a single entity (name + address + identifier is stronger
  than name alone).
- Whether the matched entity is a direct sanctions/PEP target or only a related
  party.
- Noise damping: many low-tier matches do not inflate the score.

The final score is always an integer in [0, 100].
"""

import math
from typing import Iterable


# Tier precedence (strongest first) and a fixed base contribution per tier.
# Fuzzy tiers use the actual match confidence as their base.
TIER_ORDER = [
    "identifier_exact",
    "name_exact",
    "name_fuzzy",
    "address_fuzzy",
    "network_2nd_degree",
]

TIER_BASE = {
    "identifier_exact": 95,
    "name_exact": 85,
    "name_fuzzy": 0,  # use confidence
    "address_fuzzy": 0,  # use confidence
    "network_2nd_degree": 40,
}

TARGET_BONUS = 10
DIVERSITY_BONUS_PER_TYPE = 5

# Tiers that are prone to noisy, high-volume hits.
NOISY_TIER_INDEX = TIER_ORDER.index("address_fuzzy")


def _best_match_for_entity(matches: list[dict]) -> dict:
    """Pick the single strongest match for an entity using tier precedence."""
    return max(
        matches,
        key=lambda m: (TIER_ORDER.index(m.get("match_type", "")), m.get("confidence", 0)),
    )


def _entity_risk_score(matches: list[dict]) -> int:
    """Compute a 0-100 risk contribution for one entity."""
    best = _best_match_for_entity(matches)
    tier = best.get("match_type", "")

    base = TIER_BASE.get(tier)
    if base is None or tier in ("name_fuzzy", "address_fuzzy"):
        # Fuzzy tiers use the observed similarity as the base.
        base = best.get("confidence", 0)

    is_target = bool(best.get("entity", {}).get("is_target", False))
    target_bonus = TARGET_BONUS if is_target else 0

    distinct_types = len(set(m.get("match_type", "") for m in matches))
    diversity_bonus = DIVERSITY_BONUS_PER_TYPE * (distinct_types - 1)

    return min(100, base + target_bonus + diversity_bonus)


def calculate_case_risk_score(matches: Iterable[dict]) -> int:
    """Return an integer risk score in [0, 100] for a case.

    ``matches`` should be an iterable of dict-like objects with keys:
      - entity_id
      - match_type
      - confidence
      - entity (optional dict with ``is_target`` boolean)
    """
    matches = list(matches)
    if not matches:
        return 0

    by_entity: dict[int, list[dict]] = {}
    for m in matches:
        by_entity.setdefault(m.get("entity_id"), []).append(m)

    entity_scores = []
    best_tier_index = len(TIER_ORDER) - 1  # start at weakest

    for entity_matches in by_entity.values():
        score = _entity_risk_score(entity_matches)
        entity_scores.append(score)

        best = _best_match_for_entity(entity_matches)
        tier_index = TIER_ORDER.index(best.get("match_type", ""))
        if tier_index < best_tier_index:
            best_tier_index = tier_index

    max_score = max(entity_scores)

    # Noise damping: a large number of low-tier matches (usually shared broad
    # addresses) should not produce a top-tier-looking score.
    num_entities = len(by_entity)
    if best_tier_index >= NOISY_TIER_INDEX and num_entities > 10:
        # log(128) ~ 4.85 -> damping ~ 0.51, which turns 100 -> 51.
        damping = max(0.2, 1 - math.log(num_entities) / 10)
        max_score = int(max_score * damping)

    return max(0, min(100, int(max_score)))
