"""Address-quality scoring for fuzzy address matching.

OpenSanctions addresses are free-text and frequently extremely broad ("Hong Kong",
"Russia", "Moscow"). Matching against those strings produces large, low-signal
hit lists. This module scores an address string for specificity and applies a
confidence penalty when it is too broad.

The scoring is intentionally simple and conservative:

- Empty strings are invalid / broad.
- A small denylist of known broad terms (countries, major cities, etc.) is
  treated as maximally broad.
- Addresses containing digits (street numbers, postal codes, suite numbers) are
  treated as specific.
- Addresses with several tokens but no digits are treated as moderately specific;
  they may be city+country or street+city pairs in different languages.
- Short, digit-less addresses are treated as broad.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AddressQualityResult:
    """Quality assessment for one address string."""

    score: float  # 0.0 (broad) to 1.0 (specific)
    is_broad: bool
    reason: str


# Terms that are so generic they should never drive a high-confidence match.
# Kept minimal; the heuristic below catches most broad strings without needing
# an exhaustive gazetteer.
_BROAD_TERMS = {
    "hong kong",
    "russia",
    "russian federation",
    "singapore",
    "china",
    "united states",
    "usa",
    "us",
    "united kingdom",
    "uk",
    "iran",
    "uae",
    "united arab emirates",
    "moscow",
    "beijing",
    "new york",
    "london",
    "philadelphia",
    "unknown",
    "n/a",
    "na",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def assess_address_quality(full_text: str) -> AddressQualityResult:
    """Return a quality score for ``full_text``.

    The result is used by the matcher to discount fuzzy address matches that
    are driven by overly generic addresses.
    """
    normalized = _normalize(full_text)

    if not normalized:
        return AddressQualityResult(score=0.0, is_broad=True, reason="empty")

    if normalized in _BROAD_TERMS:
        return AddressQualityResult(
            score=0.1, is_broad=True, reason=f"broad term: {normalized}"
        )

    # Digits are a strong proxy for specificity: street numbers, suites,
    # postal codes, building numbers, etc.
    if re.search(r"\d", normalized):
        return AddressQualityResult(score=1.0, is_broad=False, reason="contains number")

    tokens = normalized.split()

    # Several tokens without digits may be a full address in another language
    # (e.g. "Moscow, Russian Federation") or a street + city pair.
    if len(tokens) >= 3:
        return AddressQualityResult(score=0.7, is_broad=False, reason="multi-token")

    # One or two tokens with no digits is usually just a city or country.
    return AddressQualityResult(
        score=0.3, is_broad=True, reason="short and numberless"
    )


def apply_address_penalty(raw_confidence: int, quality: AddressQualityResult) -> int:
    """Scale ``raw_confidence`` by ``quality.score`` and clamp to [0, 100]."""
    adjusted = int(raw_confidence * quality.score)
    return max(0, min(100, adjusted))
