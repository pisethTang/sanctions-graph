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

    def test_network_falls_back_to_live_rebuild_without_snapshot(
        self, api_client, putin_entity
    ):
        # Cases written before snapshots existed have network_snapshot = {};
        # the endpoint must rebuild the graph live instead of returning nothing.
        agent = Agent.objects.create(name="Vladimir Putin", nationality="ru")
        screen_response = api_client.post("/api/screen/", {
            "agent_id": agent.id,
            "identifiers": [("passport", "75NO123456")],
        }, format="json")
        case_id = screen_response.data["case"]["id"]

        case = ScreeningCase.objects.get(id=case_id)
        case.network_snapshot = {}
        case.save(update_fields=["network_snapshot"])

        response = api_client.get(f"/api/cases/{case_id}/network/")
        assert response.status_code == 200
        node_ids = {node["data"]["id"] for node in response.data["nodes"]}
        assert f"agent-{agent.id}" in node_ids
        assert f"entity-{putin_entity.id}" in node_ids
        # The agent-to-entity edge carries the match type and a UI category.
        labels = {edge["data"]["label"] for edge in response.data["edges"]}
        assert "identifier_exact" in labels
        categories = {edge["data"]["category"] for edge in response.data["edges"]}
        assert "identifier_address" in categories

    def test_network_categorises_name_matches(self, api_client, putin_entity):
        agent = Agent.objects.create(name="Vladimir Putin", nationality="ru")
        screen_response = api_client.post("/api/screen/", {
            "agent_id": agent.id,
        }, format="json")
        case_id = screen_response.data["case"]["id"]

        response = api_client.get(f"/api/cases/{case_id}/network/")
        assert response.status_code == 200
        name_edges = [
            edge for edge in response.data["edges"]
            if edge["data"]["label"].startswith("name")
        ]
        assert name_edges
        assert all(edge["data"]["category"] == "name" for edge in name_edges)

    def test_network_links_entities_with_shared_address_or_identifier(
        self, api_client, putin_entity
    ):
        # Two matched entities that share an address and an identifier should be
        # joined by shared_address and shared_identifier edges respectively.
        other = SanctionedEntity.objects.create(
            name="Linked Entity",
            entity_type="organization",
            source_id="NK-test-linked",
        )
        EntityAddress.objects.create(
            entity=other, full_text="Moscow, Russia", country_code="ru"
        )
        EntityIdentifier.objects.create(
            entity=other,
            id_type="passport",
            value_hash=EntityIdentifier.hash_value("75NO123456"),
        )

        agent = Agent.objects.create(name="Vladimir Putin", nationality="ru")
        screen_response = api_client.post("/api/screen/", {
            "agent_id": agent.id,
            "identifiers": [("passport", "75NO123456")],
        }, format="json")
        case_id = screen_response.data["case"]["id"]

        response = api_client.get(f"/api/cases/{case_id}/network/")
        assert response.status_code == 200
        labels = {edge["data"]["label"] for edge in response.data["edges"]}
        assert "shared_address" in labels
        assert "shared_identifier" in labels
        # Entity-to-entity shared edges are grouped under one UI category.
        assert all(
            edge["data"]["category"] == "shared"
            for edge in response.data["edges"]
            if edge["data"]["label"].startswith("shared_")
        )