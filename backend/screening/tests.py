from django.test import TestCase

# Create your tests here.
import pytest
from screening.models import (
    Agent, SanctionedEntity, EntityAlias, EntityAddress,
    EntityIdentifier, ScreeningCase, Match
)


class TestEntityIdentifierHash:
    """Identifier hashing must be deterministic and case-insensitive."""

    def test_hash_is_deterministic(self):
        h1 = EntityIdentifier.hash_value("X123456")
        h2 = EntityIdentifier.hash_value("X123456")
        assert h1 == h2

    def test_hash_is_case_insensitive(self):
        h1 = EntityIdentifier.hash_value("x123456")
        h2 = EntityIdentifier.hash_value("X123456")
        assert h1 == h2

    def test_hash_strips_whitespace(self):
        h1 = EntityIdentifier.hash_value("  X123456  ")
        h2 = EntityIdentifier.hash_value("X123456")
        assert h1 == h2


class TestSanctionedEntityModel:
    def test_entity_creation(self, db):
        entity = SanctionedEntity.objects.create(
            name="Test Person",
            entity_type="person",
            source_id="NK-test-001"
        )
        assert entity.id is not None
        assert entity.entity_type == "person"

    def test_source_id_is_unique(self, db):
        SanctionedEntity.objects.create(
            name="First",
            entity_type="person",
            source_id="NK-dup"
        )
        with pytest.raises(Exception):
            SanctionedEntity.objects.create(
                name="Second",
                entity_type="person",
                source_id="NK-dup"
            )


class TestIngestionParsing:
    """Test the parsing logic from ingest_opensanctions without touching the DB."""

    def test_schema_filter_accepts_person(self):
        from screening.management.commands.ingest_opensanctions import SCHEMA_TO_ENTITY_TYPE
        assert SCHEMA_TO_ENTITY_TYPE.get("Person") == "person"

    def test_schema_filter_rejects_vessel(self):
        from screening.management.commands.ingest_opensanctions import SCHEMA_TO_ENTITY_TYPE
        assert SCHEMA_TO_ENTITY_TYPE.get("Vessel") is None

    def test_identifier_property_mapping(self):
        from screening.management.commands.ingest_opensanctions import IDENTIFIER_PROPERTIES
        assert IDENTIFIER_PROPERTIES["passportNumber"] == "passport"
        assert IDENTIFIER_PROPERTIES["leiCode"] == "other"


class TestAgentModel:
    def test_agent_creation(self, db):
        agent = Agent.objects.create(
            name="Test Agent",
            aliases=["TA", "Test"],
            nationality="au"
        )
        assert agent.name == "Test Agent"
        assert agent.aliases == ["TA", "Test"]