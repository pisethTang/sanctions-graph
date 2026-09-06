import pytest
from screening.models import (
    Agent, SanctionedEntity, EntityAlias, EntityAddress,
    EntityIdentifier, ScreeningCase, Match
)


@pytest.fixture
def sample_entity(db):
    """A sanctioned entity with one alias and one address."""
    entity = SanctionedEntity.objects.create(
        name="Vladimir Putin",
        entity_type="person",
        source_id="NK-test-001"
    )
    EntityAlias.objects.create(entity=entity, text="Vladimir Vladimirovich Putin")
    EntityAddress.objects.create(entity=entity, full_text="Moscow, Russia", country_code="ru")
    return entity


@pytest.fixture
def sample_agent(db):
    """An education agent."""
    return Agent.objects.create(
        name="ABC Education Ltd",
        aliases=["ABC Ed", "ABC Edu"],
        nationality="sg"
    )