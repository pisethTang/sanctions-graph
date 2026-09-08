"""Tests for integrating the OpenSanctions ``target`` flag end-to-end.

OpenSanctions sets ``target: true`` on the person or organization that is itself
sanctioned or a PEP, and ``target: false`` on related parties (family members,
subsidiaries, associates, etc.). The product's risk score should treat a match
against a direct target as more serious than a match against a related entity.

This suite tests:
  - the model field exists and defaults to False
  - the ingestion parser captures the flag
  - the screening API enriches match results with the flag
  - the case risk score is higher when a target entity is hit
"""

import pytest
from rest_framework.test import APIClient

from screening.models import Agent, SanctionedEntity, EntityAlias


@pytest.fixture
def api_client():
    return APIClient()


class TestSanctionedEntityTargetFlag:
    """SanctionedEntity.is_target persists the OpenSanctions target flag."""

    def test_is_target_defaults_to_false(self, db):
        entity = SanctionedEntity.objects.create(
            name="Related Party",
            entity_type="person",
            source_id="NK-related",
        )
        assert entity.is_target is False

    def test_is_target_can_be_true(self, db):
        entity = SanctionedEntity.objects.create(
            name="Sanctioned Person",
            entity_type="person",
            source_id="NK-target",
            is_target=True,
        )
        assert entity.is_target is True


class TestIngestionTargetFlag:
    """The ingest command maps FtM ``target`` onto SanctionedEntity.is_target."""

    def test_parse_entity_records_target_true(self):
        from screening.management.commands.ingest_opensanctions import Command

        cmd = Command()
        record = cmd.parse_entity({
            "id": "NK-target",
            "schema": "Person",
            "properties": {"name": ["Vladimir Putin"]},
            "target": True,
        })
        assert record["is_target"] is True

    def test_parse_entity_records_target_false(self):
        from screening.management.commands.ingest_opensanctions import Command

        cmd = Command()
        record = cmd.parse_entity({
            "id": "NK-related",
            "schema": "Person",
            "properties": {"name": ["Maria Putin"]},
            "target": False,
        })
        assert record["is_target"] is False

    def test_parse_entity_defaults_target_to_false_when_missing(self):
        from screening.management.commands.ingest_opensanctions import Command

        cmd = Command()
        record = cmd.parse_entity({
            "id": "NK-noflag",
            "schema": "Person",
            "properties": {"name": ["Ivan Ivanov"]},
        })
        assert record["is_target"] is False


class TestScreeningUsesTargetFlag:
    """The screening API considers is_target when computing case.risk_score."""

    def test_target_match_scores_higher_than_related_match(self, db, api_client):
        # Two entities with the same name match type/confidence, but one is a target.
        target = SanctionedEntity.objects.create(
            name="Alex Target",
            entity_type="person",
            source_id="NK-target",
            is_target=True,
        )
        related = SanctionedEntity.objects.create(
            name="Alex Related",
            entity_type="person",
            source_id="NK-related",
            is_target=False,
        )
        # Aliases so both match the same agent name.
        EntityAlias.objects.create(entity=target, text="Alex Demo")
        EntityAlias.objects.create(entity=related, text="Alex Demo")

        agent = Agent.objects.create(name="Alex Demo", nationality="ru")

        response = api_client.post("/api/screen/", {
            "agent_id": agent.id,
        }, format="json")

        assert response.status_code == 201
        case = response.data["case"]
        matches = response.data["matches"]

        # Both entities should have been found.
        assert len(matches) == 2

        # The match against the target entity should carry is_target=true.
        target_match = next(m for m in matches if m["source_id"] == "NK-target")
        related_match = next(m for m in matches if m["source_id"] == "NK-related")
        assert target_match["entity_name"] == "Alex Target"
        assert related_match["entity_name"] == "Alex Related"
        assert target_match["is_target"] is True
        assert related_match["is_target"] is False

        # Because one hit is a target, the case risk score should exceed a
        # related-only hit (which would be 87 for name_exact without target bonus).
        assert case["risk_score"] > 90
