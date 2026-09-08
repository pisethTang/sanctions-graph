"""Tests for the case-level risk-scoring model.

Why this matters:
  The current risk_score is simply max(match.confidence). That means a single
  low-quality address match ("Hong Kong" -> 100 fuzzy entities) produces the
  same score as a passport exact match. It also ignores:

  - match diversity (name + address + identifier is stronger than address alone)
  - whether the matched entity is a direct target or only a related party
  - the number of distinct entities hit (noise)

  calculate_case_risk_score() should combine these signals into a single
  0-100 score that reflects how suspicious the overall case actually is.
"""

import pytest

from screening.models import Agent, EntityIdentifier, SanctionedEntity


@pytest.fixture
def risk_scoring():
    try:
        from screening import risk_scoring as rs
        return rs
    except ImportError as exc:
        raise ImportError(
            "screening.risk_scoring module does not exist yet. "
            "Create it with calculate_case_risk_score(matches) before running these tests."
        ) from exc


class TestBasicScoring:
    """Sanity checks for the 0-100 score."""

    def test_empty_match_list_scores_zero(self, risk_scoring):
        assert risk_scoring.calculate_case_risk_score([]) == 0

    def test_single_identifier_exact_is_max_risk(self, risk_scoring):
        matches = [
            {
                "entity_id": 1,
                "match_type": "identifier_exact",
                "confidence": 100,
                "entity": {"is_target": True},
            }
        ]
        assert risk_scoring.calculate_case_risk_score(matches) == 100

    def test_single_name_exact_is_high_risk(self, risk_scoring):
        matches = [
            {
                "entity_id": 1,
                "match_type": "name_exact",
                "confidence": 95,
                "entity": {"is_target": True},
            }
        ]
        assert risk_scoring.calculate_case_risk_score(matches) >= 90


class TestMatchDiversity:
    """Multiple evidence types should score higher than one alone."""

    def test_name_plus_identifier_beats_name_alone(self, risk_scoring):
        name_only = [
            {
                "entity_id": 1,
                "match_type": "name_exact",
                "confidence": 95,
                "entity": {"is_target": True},
            }
        ]
        name_and_id = [
            {
                "entity_id": 1,
                "match_type": "name_exact",
                "confidence": 95,
                "entity": {"is_target": True},
            },
            {
                "entity_id": 1,
                "match_type": "identifier_exact",
                "confidence": 100,
                "entity": {"is_target": True},
            },
        ]
        assert risk_scoring.calculate_case_risk_score(name_and_id) > risk_scoring.calculate_case_risk_score(name_only)

    def test_name_plus_address_beats_address_alone(self, risk_scoring):
        address_only = [
            {
                "entity_id": 1,
                "match_type": "address_fuzzy",
                "confidence": 80,
                "entity": {"is_target": True},
            }
        ]
        name_and_address = [
            {
                "entity_id": 1,
                "match_type": "address_fuzzy",
                "confidence": 80,
                "entity": {"is_target": True},
            },
            {
                "entity_id": 1,
                "match_type": "name_exact",
                "confidence": 95,
                "entity": {"is_target": True},
            },
        ]
        assert (
            risk_scoring.calculate_case_risk_score(name_and_address)
            > risk_scoring.calculate_case_risk_score(address_only)
        )


class TestTargetVsRelated:
    """Matches against direct targets should score higher than related parties."""

    def test_target_entity_increases_score(self, risk_scoring):
        target_match = [
            {
                "entity_id": 1,
                "match_type": "name_exact",
                "confidence": 95,
                "entity": {"is_target": True},
            }
        ]
        related_match = [
            {
                "entity_id": 2,
                "match_type": "name_exact",
                "confidence": 95,
                "entity": {"is_target": False},
            }
        ]
        assert risk_scoring.calculate_case_risk_score(target_match) > risk_scoring.calculate_case_risk_score(related_match)


class TestNoiseCap:
    """Many low-quality matches should not inflate the score."""

    def test_many_broad_address_matches_do_not_max_out_score(self, risk_scoring):
        # Simulate the "Hong Kong" case: 128 address_fuzzy matches at confidence 100.
        matches = [
            {
                "entity_id": i,
                "match_type": "address_fuzzy",
                "confidence": 100,
                "entity": {"is_target": False},
            }
            for i in range(1, 129)
        ]
        score = risk_scoring.calculate_case_risk_score(matches)
        assert score < 100
        assert score < 80  # Broad-address noise should not feel like a passport hit.

    def test_many_network_second_degree_matches_do_not_max_out_score(self, risk_scoring):
        matches = [
            {
                "entity_id": i,
                "match_type": "network_2nd_degree",
                "confidence": 50,
                "entity": {"is_target": False},
            }
            for i in range(1, 101)
        ]
        score = risk_scoring.calculate_case_risk_score(matches)
        assert score < 100
        assert score < 75


class TestTierPrecedence:
    """Stronger evidence should dominate weaker evidence."""

    def test_identifier_exact_dominates_many_address_hits(self, risk_scoring):
        matches = [
            {
                "entity_id": 1,
                "match_type": "identifier_exact",
                "confidence": 100,
                "entity": {"is_target": True},
            }
        ] + [
            {
                "entity_id": i,
                "match_type": "address_fuzzy",
                "confidence": 100,
                "entity": {"is_target": False},
            }
            for i in range(2, 130)
        ]
        score = risk_scoring.calculate_case_risk_score(matches)
        assert score == 100


class TestScoreRange:
    """The score must always be an integer in [0, 100]."""

    def test_score_is_integer_between_zero_and_one_hundred(self, risk_scoring):
        matches = [
            {
                "entity_id": 1,
                "match_type": "name_fuzzy",
                "confidence": 67,
                "entity": {"is_target": False},
            }
        ]
        score = risk_scoring.calculate_case_risk_score(matches)
        assert isinstance(score, int)
        assert 0 <= score <= 100
