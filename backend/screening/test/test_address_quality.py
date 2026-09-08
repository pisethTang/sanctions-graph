"""Tests for address-quality scoring.

Why this matters:
  OpenSanctions addresses are free-text and often extremely broad ("Hong Kong",
  "Russia", "Moscow"). Feeding those into the fuzzy matcher produces large,
  low-signal hit lists that look alarming but are mostly false positives.

  The address-quality layer scores an address string before it is used for
  matching. Broad strings are flagged and their match confidence is discounted.
  Specific strings keep full weight.

  The matching engine will call this layer automatically; these tests exercise
  the scoring function in isolation.
"""

import pytest

from screening.models import Agent, EntityAddress, SanctionedEntity


# The scoring function will live in screening.address_quality.
# Import it lazily via a fixture so the tests fail cleanly if the module is missing.
@pytest.fixture
def address_quality():
    try:
        from screening import address_quality as aq
        return aq
    except ImportError as exc:
        raise ImportError(
            "screening.address_quality module does not exist yet. "
            "Create it with assess_address_quality(full_text) before running these tests."
        ) from exc


class TestAddressQualityScoring:
    """score_address_quality returns 0.0 (broad) to 1.0 (specific)."""

    def test_country_only_address_is_broad(self, address_quality):
        result = address_quality.assess_address_quality("Hong Kong")
        assert result.is_broad is True
        assert result.score < 0.5

    def test_another_country_only_address_is_broad(self, address_quality):
        result = address_quality.assess_address_quality("Russia")
        assert result.is_broad is True

    def test_city_only_address_is_broad(self, address_quality):
        result = address_quality.assess_address_quality("Moscow")
        assert result.is_broad is True

    def test_street_address_is_specific(self, address_quality):
        result = address_quality.assess_address_quality(
            "Suite 1201, 88 Collyer Quay, Singapore 049320"
        )
        assert result.is_broad is False
        assert result.score == pytest.approx(1.0, abs=0.1)

    def test_address_with_street_and_city_is_specific(self, address_quality):
        result = address_quality.assess_address_quality(
            "Tower A, Beijing Finance Center, Chaoyang"
        )
        assert result.is_broad is False
        assert result.score >= 0.7

    def test_whitespace_and_case_are_normalized(self, address_quality):
        r1 = address_quality.assess_address_quality("  hong kong  ")
        r2 = address_quality.assess_address_quality("HONG KONG")
        assert r1.score == pytest.approx(r2.score, abs=0.01)
        assert r1.is_broad == r2.is_broad

    def test_empty_address_is_broad(self, address_quality):
        result = address_quality.assess_address_quality("")
        assert result.is_broad is True
        assert result.score == 0.0


class TestConfidencePenalty:
    """Broad addresses reduce the confidence of address_fuzzy matches."""

    def test_broad_address_reduces_match_confidence(self, address_quality):
        raw_confidence = 100
        quality = address_quality.assess_address_quality("Hong Kong")
        adjusted = address_quality.apply_address_penalty(raw_confidence, quality)
        assert adjusted < raw_confidence
        assert adjusted < 80

    def test_specific_address_keeps_full_confidence(self, address_quality):
        raw_confidence = 100
        quality = address_quality.assess_address_quality(
            "Suite 1201, 88 Collyer Quay, Singapore 049320"
        )
        adjusted = address_quality.apply_address_penalty(raw_confidence, quality)
        assert adjusted == raw_confidence

    def test_penalty_never_drops_below_zero(self, address_quality):
        quality = address_quality.assess_address_quality("Hong Kong")
        adjusted = address_quality.apply_address_penalty(10, quality)
        assert adjusted >= 0


class TestMatcherIntegration:
    """The matcher uses address quality when producing address_fuzzy hits."""

    def test_broad_agent_address_produces_reduced_confidence(self, db, address_quality):
        from screening.matcher import ScreenMatcher

        entity = SanctionedEntity.objects.create(
            name="Generic HK Company",
            entity_type="organization",
            source_id="NK-hk-generic",
        )
        EntityAddress.objects.create(
            entity=entity,
            full_text="Hong Kong",
            country_code="hk",
        )

        agent = Agent.objects.create(
            name="Asia Power Consulting",
            nationality="hk",
            addresses=[{"full_text": "Hong Kong", "country_code": "hk"}],
        )

        matches = ScreenMatcher().screen(agent)
        address_hits = [m for m in matches if m["match_type"] == "address_fuzzy"]
        assert len(address_hits) == 1
        assert address_hits[0]["confidence"] < 100

    def test_specific_agent_address_keeps_full_confidence(self, db):
        from screening.matcher import ScreenMatcher

        entity = SanctionedEntity.objects.create(
            name="Wong & Associates Pte Ltd",
            entity_type="organization",
            source_id="NK-wong-specific",
        )
        EntityAddress.objects.create(
            entity=entity,
            full_text="Suite 1201, 88 Collyer Quay, Singapore 049320",
            country_code="sg",
        )

        agent = Agent.objects.create(
            name="Some Agent",
            nationality="sg",
            addresses=[{
                "full_text": "Suite 1201, 88 Collyer Quay, Singapore 049320",
                "country_code": "sg",
            }],
        )

        matches = ScreenMatcher().screen(agent)
        address_hits = [m for m in matches if m["match_type"] == "address_fuzzy"]
        assert len(address_hits) == 1
        assert address_hits[0]["confidence"] == 100
