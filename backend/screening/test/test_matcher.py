import networkx as nx
import pytest
from django.db import connection

from screening.models import (
    Agent,
    EntityAddress,
    EntityAlias,
    EntityIdentifier,
    SanctionedEntity,
)
from screening.matcher import ScreenMatcher


@pytest.fixture
def sanctioned_person(db):
    """A sanctioned person with alias, address, and passport."""
    entity = SanctionedEntity.objects.create(
        name="Vladimir Putin",
        entity_type="person",
        source_id="NK-test-putin",
    )
    EntityAlias.objects.create(entity=entity, text="Vladimir Vladimirovich Putin")
    EntityAddress.objects.create(
        entity=entity, full_text="Moscow, Russia", country_code="ru"
    )
    EntityIdentifier.objects.create(
        entity=entity,
        id_type="passport",
        value_hash=EntityIdentifier.hash_value("75NO123456"),
    )
    return entity


@pytest.fixture
def sanctioned_associate(db):
    """A sanctioned person who shares an address with the first person."""
    entity = SanctionedEntity.objects.create(
        name="Yevgeny Prigozhin",
        entity_type="person",
        source_id="NK-test-prigozhin",
    )
    EntityAlias.objects.create(entity=entity, text="Yevgeny Viktorovich Prigozhin")
    # Same address as Putin — this creates the 2nd-degree link
    EntityAddress.objects.create(
        entity=entity, full_text="Moscow, Russia", country_code="ru"
    )
    EntityAddress.objects.create(
            entity=entity, full_text="Saint Petersburg, Russia", country_code="ru"
        )


    return entity


@pytest.fixture
def clean_agent(db):
    """An agent with no sanctions risk."""
    return Agent.objects.create(
        name="Clean Education Ltd",
        aliases=["Clean Ed"],
        nationality="au",
    )


@pytest.fixture
def risky_agent(db):
    """An agent that matches Putin by name and shares an address with Prigozhin."""
    agent = Agent.objects.create(
        name="Vladimir Putin",
        aliases=["Putin Education"],
        nationality="ru",
    )
    # We will attach identifiers and addresses during tests
    return agent


class TestNoMatches:
    def test_clean_agent_returns_empty_list(self, clean_agent):
        matcher = ScreenMatcher()
        matches = matcher.screen(clean_agent)
        assert matches == []


class TestIdentifierExactMatch:
    def test_passport_match_100_percent(self, sanctioned_person, risky_agent):
        # Give the agent the exact same passport number
        matcher = ScreenMatcher()
        matches = matcher.screen(
            risky_agent, identifiers=[("passport", "75NO123456")]
        )
        assert len(matches) == 1
        assert matches[0]["match_type"] == "identifier_exact"
        assert matches[0]["confidence"] == 100
        assert matches[0]["entity_id"] == sanctioned_person.id

    def test_tax_id_match_100_percent(self, db, sanctioned_person):
        # Add a tax ID to the sanctioned entity
        EntityIdentifier.objects.create(
            entity=sanctioned_person,
            id_type="tax_id",
            value_hash=EntityIdentifier.hash_value("TAX-777888"),
        )
        agent = Agent.objects.create(name="Some Agent", nationality="ru")
        matcher = ScreenMatcher()
        matches = matcher.screen(agent, identifiers=[("tax_id", "TAX-777888")])
        assert len(matches) == 1
        assert matches[0]["match_type"] == "identifier_exact"
        assert matches[0]["confidence"] == 100


class TestNameExactMatch:
    def test_primary_name_exact(self, sanctioned_person, risky_agent):
        matcher = ScreenMatcher()
        matches = matcher.screen(risky_agent)
        # Should find the exact name match
        exact_matches = [m for m in matches if m["match_type"] == "name_exact"]
        assert len(exact_matches) == 1
        assert exact_matches[0]["confidence"] == 95
        assert exact_matches[0]["entity_id"] == sanctioned_person.id

    def test_alias_exact_match(self, db, sanctioned_person):
        agent = Agent.objects.create(
            name="Random Name",
            aliases=["Vladimir Vladimirovich Putin"],  # exact alias match
            nationality="ru",
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        exact_matches = [m for m in matches if m["match_type"] == "name_exact"]
        assert len(exact_matches) == 1
        assert exact_matches[0]["entity_id"] == sanctioned_person.id


class TestNameFuzzyMatch:
    def test_typo_in_name(self, db, sanctioned_person):
        # "Putni" is a typo of "Putin"
        agent = Agent.objects.create(
            name="Vladimir Putni",
            nationality="ru",
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        fuzzy_matches = [m for m in matches if m["match_type"] == "name_fuzzy"]
        assert len(fuzzy_matches) == 1
        assert fuzzy_matches[0]["entity_id"] == sanctioned_person.id
        assert 60 <= fuzzy_matches[0]["confidence"] <= 90

    def test_transliteration_variant(self, db):
        entity = SanctionedEntity.objects.create(
            name="Sergei Lavrov",
            entity_type="person",
            source_id="NK-test-lavrov",
        )
        EntityAlias.objects.create(entity=entity, text="Sergey Lavrov")
        agent = Agent.objects.create(
            name="Sergey Lavrov",  # "Sergey" vs "Sergei"
            nationality="ru",
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        # Could be exact or fuzzy depending on pg_trgm threshold
        name_matches = [m for m in matches if "name" in m["match_type"]]
        assert len(name_matches) >= 1


class TestAddressFuzzyMatch:
    def test_similar_address(self, db, sanctioned_person):
        agent = Agent.objects.create(
            name="Address Agent",
            nationality="ru",
            addresses=[{"full_text": "Moscow, Russian Federation", "country_code": "ru"}],
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        addr_matches = [m for m in matches if m["match_type"] == "address_fuzzy"]
        assert len(addr_matches) == 1
        assert addr_matches[0]["entity_id"] == sanctioned_person.id
        assert 30 <= addr_matches[0]["confidence"] <= 70


class TestSecondDegreeNetwork:
    def test_shared_address_two_hops(self, sanctioned_person, sanctioned_associate):
        # Agent shares address with Prigozhin
        # Prigozhin shares address with Putin
        # So Agent is 2 hops from Putin
        agent = Agent.objects.create(
            name="Network Agent",
            nationality="ru",
            addresses=[{"full_text": "Saints Petersburg, Russia", "country_code": "ru"}],
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        network_matches = [
            m for m in matches if m["match_type"] == "network_2nd_degree"
        ]
        # Should find Putin as 2nd-degree via Prigozhin
        putin_match = [m for m in network_matches if m["entity_id"] == sanctioned_person.id]
        assert len(putin_match) == 1
        assert 40 <= putin_match[0]["confidence"] <= 70


class TestDeduplication:
    def test_same_entity_found_by_name_and_identifier(self, sanctioned_person):
        # Agent matches by both name AND passport
        agent = Agent.objects.create(
            name="Vladimir Putin",
            aliases=[],
            nationality="ru",
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(
            agent, identifiers=[("passport", "75NO123456")]
        )
        # Should only return ONE match for Putin, not two
        putin_matches = [m for m in matches if m["entity_id"] == sanctioned_person.id]
        assert len(putin_matches) == 1
        # Should keep the highest confidence (identifier_exact = 100, not name_exact = 95)
        assert putin_matches[0]["match_type"] == "identifier_exact"
        assert putin_matches[0]["confidence"] == 100


class TestEdgeCases:
    def test_agent_with_no_identifiers(self, clean_agent):
        matcher = ScreenMatcher()
        matches = matcher.screen(clean_agent)
        assert matches == []

    def test_agent_with_empty_aliases(self, db):
        entity = SanctionedEntity.objects.create(
            name="Only Name",
            entity_type="person",
            source_id="NK-only",
        )
        agent = Agent.objects.create(name="Only Name", aliases=[], nationality="au")
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        assert len(matches) == 1
        assert matches[0]["match_type"] == "name_exact"

    def test_case_insensitive_name_match(self, db, sanctioned_person):
        agent = Agent.objects.create(
            name="vladimir putin",  # lowercase
            nationality="ru",
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        exact_matches = [m for m in matches if m["match_type"] == "name_exact"]
        assert len(exact_matches) == 1


class TestBlankAndEmptyInputs:
    """Blank names and empty addresses are skipped, never queried."""

    def test_whitespace_alias_is_skipped_by_name_tiers(self, db, sanctioned_person):
        # A whitespace-only alias is truthy, so it reaches the strip() guard in
        # both _name_exact_matches and _name_fuzzy_matches; both must skip it.
        agent = Agent.objects.create(
            name="Unrelated Person",
            aliases=[" ", "   "],
            nationality="ru",
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        assert matches == []

    def test_empty_address_string_is_skipped(self, db, sanctioned_person):
        # _agent_addresses normally filters empty strings out, but the
        # address tier guards against them too; exercise that guard directly.
        matcher = ScreenMatcher()
        assert matcher._address_fuzzy_matches([""]) == []

    def test_plain_string_addresses_are_tolerated(self, db, sanctioned_person):
        # Agent.addresses is documented as a list of dicts, but plain strings
        # must be accepted as well.
        agent = Agent.objects.create(
            name="String Address Agent",
            nationality="ru",
            addresses=["Moscow, Russian Federation"],
        )
        matcher = ScreenMatcher()
        matches = matcher.screen(agent)
        addr_matches = [m for m in matches if m["match_type"] == "address_fuzzy"]
        assert len(addr_matches) == 1
        assert addr_matches[0]["entity_id"] == sanctioned_person.id


class TestSharedAttributeEdges:
    def test_empty_frontier_returns_no_neighbours(self, db):
        # The network walk calls this with an empty frontier on its last pass;
        # it must short-circuit instead of querying with an empty IN list.
        matcher = ScreenMatcher()
        graph = nx.Graph()
        assert matcher._shared_attribute_edges(set(), graph) == set()
        assert graph.number_of_edges() == 0


class TestCollect:
    """_collect keeps the strongest tier per entity, then highest confidence."""

    def test_higher_confidence_same_tier_replaces_weaker_match(self):
        # Within one tier an entity can be hit twice with different trigram
        # scores; the higher score must win.
        found = {}
        weaker = {
            "entity_id": 1,
            "match_type": "name_fuzzy",
            "confidence": 70,
            "explanation": "weaker",
        }
        stronger = {
            "entity_id": 1,
            "match_type": "name_fuzzy",
            "confidence": 85,
            "explanation": "stronger",
        }
        ScreenMatcher._collect(found, [weaker])
        ScreenMatcher._collect(found, [stronger])
        assert found[1]["confidence"] == 85
        assert found[1]["explanation"] == "stronger"