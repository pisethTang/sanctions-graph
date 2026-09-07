import pytest
from rest_framework.test import APIClient

from screening.models import (
    Agent, SanctionedEntity, EntityAlias, EntityAddress,
    EntityIdentifier, ScreeningCase, Match
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def putin_entity(db):
    entity = SanctionedEntity.objects.create(
        name="Vladimir Putin",
        entity_type="person",
        source_id="NK-test-putin",
    )
    EntityAlias.objects.create(entity=entity, text="Vladimir Vladimirovich Putin")
    EntityAddress.objects.create(entity=entity, full_text="Moscow, Russia", country_code="ru")
    EntityIdentifier.objects.create(
        entity=entity,
        id_type="passport",
        value_hash=EntityIdentifier.hash_value("75NO123456"),
    )
    return entity


class TestAgentCreation:
    def test_create_agent(self, db, api_client):
        response = api_client.post("/api/agents/", {
            "name": "ABC Education Ltd",
            "aliases": ["ABC Ed"],
            "nationality": "sg",
            "birth_date": "1990-01-01",
            "addresses": [{"full_text": "Singapore", "country_code": "sg"}],
        }, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "ABC Education Ltd"
        assert Agent.objects.count() == 1


class TestScreening:
    def test_screen_agent_returns_case_and_matches(self, api_client, putin_entity):
        # Create agent first
        agent_response = api_client.post("/api/agents/", {
            "name": "Vladimir Putin",
            "aliases": [],
            "nationality": "ru",
        }, format="json")
        agent_id = agent_response.data["id"]

        # Screen the agent
        response = api_client.post("/api/screen/", {
            "agent_id": agent_id,
            "identifiers": [("passport", "75NO123456")],
        }, format="json")
        assert response.status_code == 201
        assert "case" in response.data
        assert "matches" in response.data
        assert len(response.data["matches"]) >= 1
        assert response.data["matches"][0]["match_type"] == "identifier_exact"
        assert response.data["matches"][0]["confidence"] == 100


class TestCaseList:
    def test_list_cases(self, api_client, putin_entity):
        # Create and screen an agent
        agent = Agent.objects.create(name="Test Agent", nationality="ru")
        api_client.post("/api/screen/", {"agent_id": agent.id}, format="json")

        response = api_client.get("/api/cases/")
        assert response.status_code == 200
        assert len(response.data) >= 1


class TestCaseDetail:
    def test_case_detail_with_matches(self, api_client, putin_entity):
        agent = Agent.objects.create(name="Vladimir Putin", nationality="ru")
        screen_response = api_client.post("/api/screen/", {
            "agent_id": agent.id,
            "identifiers": [("passport", "75NO123456")],
        }, format="json")
        case_id = screen_response.data["case"]["id"]

        response = api_client.get(f"/api/cases/{case_id}/")
        assert response.status_code == 200
        assert response.data["agent"]["name"] == "Vladimir Putin"
        assert len(response.data["matches"]) >= 1


class TestNetworkEndpoint:
    def test_network_returns_cytoscape_format(self, api_client, putin_entity):
        agent = Agent.objects.create(name="Vladimir Putin", nationality="ru")
        screen_response = api_client.post("/api/screen/", {
            "agent_id": agent.id,
            "identifiers": [("passport", "75NO123456")],
        }, format="json")
        case_id = screen_response.data["case"]["id"]

        response = api_client.get(f"/api/cases/{case_id}/network/")
        assert response.status_code == 200
        assert "nodes" in response.data
        assert "edges" in response.data
        assert isinstance(response.data["nodes"], list)
        assert isinstance(response.data["edges"], list)
        # Should have at least one node for the matched entity
        assert len(response.data["nodes"]) >= 1