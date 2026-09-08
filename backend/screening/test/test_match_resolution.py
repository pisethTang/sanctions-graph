"""Tests for the match resolution workflow.

Compliance officers review each match on a case and mark it as a confirmed hit
or a false positive. When every match on a case has been reviewed, the case
itself flips from "open" to "resolved"; reopening any match reopens the case.

This suite tests:
  - PATCH /api/matches/<id>/ sets resolved + resolution
  - resolution is validated against the allowed values
  - matcher-owned fields (confidence, match_type) cannot be edited
  - unknown match ids return 404
  - the case status rolls up from its matches' review state
"""

import pytest
from rest_framework.test import APIClient

from screening.models import Agent, Match, SanctionedEntity, ScreeningCase


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def case_with_matches(db):
    agent = Agent.objects.create(name="Test Agent")
    case = ScreeningCase.objects.create(agent=agent, risk_score=90)
    matches = []
    for i in range(2):
        entity = SanctionedEntity.objects.create(
            name=f"Entity {i}", entity_type="person", source_id=f"NK-e{i}"
        )
        matches.append(
            Match.objects.create(
                case=case, entity=entity, match_type="name_fuzzy", confidence=80
            )
        )
    return case, matches


class TestMatchResolutionEndpoint:
    """PATCH /api/matches/<id>/ updates the review state of one match."""

    def test_confirm_marks_match_resolved(self, api_client, case_with_matches):
        _, matches = case_with_matches
        res = api_client.patch(
            f"/api/matches/{matches[0].id}/",
            {"resolved": True, "resolution": "confirmed"},
            format="json",
        )
        assert res.status_code == 200
        assert res.data["resolved"] is True
        assert res.data["resolution"] == "confirmed"
        matches[0].refresh_from_db()
        assert matches[0].resolved is True
        assert matches[0].resolution == "confirmed"

    def test_dismiss_marks_false_positive(self, api_client, case_with_matches):
        _, matches = case_with_matches
        res = api_client.patch(
            f"/api/matches/{matches[0].id}/",
            {"resolved": True, "resolution": "false_positive"},
            format="json",
        )
        assert res.status_code == 200
        matches[0].refresh_from_db()
        assert matches[0].resolution == "false_positive"

    def test_reopen_clears_resolution(self, api_client, case_with_matches):
        _, matches = case_with_matches
        matches[0].resolved = True
        matches[0].resolution = "confirmed"
        matches[0].save()
        res = api_client.patch(
            f"/api/matches/{matches[0].id}/",
            {"resolved": False, "resolution": ""},
            format="json",
        )
        assert res.status_code == 200
        matches[0].refresh_from_db()
        assert matches[0].resolved is False
        assert matches[0].resolution == ""

    def test_invalid_resolution_rejected(self, api_client, case_with_matches):
        _, matches = case_with_matches
        res = api_client.patch(
            f"/api/matches/{matches[0].id}/",
            {"resolved": True, "resolution": "not-a-real-resolution"},
            format="json",
        )
        assert res.status_code == 400
        matches[0].refresh_from_db()
        assert matches[0].resolved is False

    def test_unknown_match_returns_404(self, api_client, db):
        res = api_client.patch(
            "/api/matches/99999/", {"resolved": True}, format="json"
        )
        assert res.status_code == 404

    def test_matcher_fields_are_not_editable(self, api_client, case_with_matches):
        _, matches = case_with_matches
        res = api_client.patch(
            f"/api/matches/{matches[0].id}/",
            {"confidence": 1, "match_type": "name_exact", "resolved": True,
             "resolution": "confirmed"},
            format="json",
        )
        assert res.status_code == 200
        matches[0].refresh_from_db()
        assert matches[0].confidence == 80
        assert matches[0].match_type == "name_fuzzy"


class TestMatchRetrieveEndpoint:
    """GET /api/matches/<id>/ returns the full read-only match representation."""

    def test_retrieve_match(self, api_client, case_with_matches):
        _, matches = case_with_matches
        res = api_client.get(f"/api/matches/{matches[0].id}/")
        assert res.status_code == 200
        assert res.data["id"] == matches[0].id
        assert res.data["match_type"] == "name_fuzzy"
        assert res.data["entity_name"] == "Entity 0"
        assert res.data["resolved"] is False


class TestCaseStatusRollup:
    """The case status follows the review state of its matches."""

    def test_case_resolves_when_all_matches_resolved(
        self, api_client, case_with_matches
    ):
        case, matches = case_with_matches
        for match in matches:
            api_client.patch(
                f"/api/matches/{match.id}/",
                {"resolved": True, "resolution": "false_positive"},
                format="json",
            )
        case.refresh_from_db()
        assert case.status == "resolved"

    def test_case_stays_open_while_matches_unreviewed(
        self, api_client, case_with_matches
    ):
        case, matches = case_with_matches
        api_client.patch(
            f"/api/matches/{matches[0].id}/",
            {"resolved": True, "resolution": "confirmed"},
            format="json",
        )
        case.refresh_from_db()
        assert case.status == "open"

    def test_case_reopens_when_a_match_is_reopened(
        self, api_client, case_with_matches
    ):
        case, matches = case_with_matches
        for match in matches:
            api_client.patch(
                f"/api/matches/{match.id}/",
                {"resolved": True, "resolution": "confirmed"},
                format="json",
            )
        api_client.patch(
            f"/api/matches/{matches[0].id}/",
            {"resolved": False, "resolution": ""},
            format="json",
        )
        case.refresh_from_db()
        assert case.status == "open"
