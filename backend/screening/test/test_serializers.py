"""Tests for serializer-level validation, exercised without HTTP.

These cover the input normalisation the API relies on:
  - MatchResolutionSerializer rejects resolutions outside the allowed choices
  - ScreenRequestSerializer rejects unknown agent ids
  - identifiers are accepted as [id_type, value] pairs or {"id_type", "value"}
    dicts, and anything else is a validation error
"""

import pytest

from screening.models import Agent
from screening.serializers import MatchResolutionSerializer, ScreenRequestSerializer


class TestMatchResolutionSerializer:
    """Resolution must be one of the allowed choices (or blank)."""

    def test_valid_resolution_is_accepted(self, db):
        serializer = MatchResolutionSerializer(
            data={"resolved": True, "resolution": "confirmed"}
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["resolution"] == "confirmed"

    def test_blank_resolution_is_accepted(self, db):
        # Reopening a match sends an empty resolution.
        serializer = MatchResolutionSerializer(
            data={"resolved": False, "resolution": ""}
        )
        assert serializer.is_valid(), serializer.errors

    def test_invalid_resolution_is_rejected(self, db):
        serializer = MatchResolutionSerializer(
            data={"resolved": True, "resolution": "maybe"}
        )
        assert serializer.is_valid() is False
        assert "resolution" in serializer.errors


class TestScreenRequestSerializer:
    """Input validation for POST /api/screen/."""

    def test_unknown_agent_id_is_rejected(self, db):
        serializer = ScreenRequestSerializer(data={"agent_id": 99999})
        assert serializer.is_valid() is False
        assert "agent_id" in serializer.errors

    def test_dict_form_identifiers_are_normalised(self, db):
        agent = Agent.objects.create(name="Test Agent")
        serializer = ScreenRequestSerializer(data={
            "agent_id": agent.id,
            "identifiers": [
                {"id_type": "passport", "value": "75NO123456"},
                {"id_type": "tax_id", "raw_value": "TAX-1"},
            ],
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["identifiers"] == [
            ("passport", "75NO123456"),
            ("tax_id", "TAX-1"),
        ]

    def test_pair_form_identifiers_are_normalised(self, db):
        agent = Agent.objects.create(name="Test Agent")
        serializer = ScreenRequestSerializer(data={
            "agent_id": agent.id,
            "identifiers": [["passport", "75NO123456"]],
        })
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["identifiers"] == [
            ("passport", "75NO123456")
        ]

    def test_malformed_identifier_shape_is_rejected(self, db):
        agent = Agent.objects.create(name="Test Agent")
        serializer = ScreenRequestSerializer(data={
            "agent_id": agent.id,
            "identifiers": ["just-a-string"],
        })
        assert serializer.is_valid() is False
        assert "identifiers" in serializer.errors

    def test_empty_identifier_value_is_rejected(self, db):
        agent = Agent.objects.create(name="Test Agent")
        serializer = ScreenRequestSerializer(data={
            "agent_id": agent.id,
            "identifiers": [["passport", ""]],
        })
        assert serializer.is_valid() is False
        assert "identifiers" in serializer.errors
