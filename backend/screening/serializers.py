"""Serializers for the screening API."""

from rest_framework import serializers

from screening.models import Agent, Match, SanctionedEntity, ScreeningCase


class AgentSerializer(serializers.ModelSerializer):
    # Identifiers are supplied at screening time, not stored on the Agent
    # (passport/tax numbers are only ever persisted as hashes on
    # EntityIdentifier). Accepted here so a client can post one payload.
    identifiers = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField()),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "aliases",
            "addresses",
            "birth_date",
            "nationality",
            "identifiers",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        validated_data.pop("identifiers", None)
        return super().create(validated_data)


class MatchSerializer(serializers.ModelSerializer):
    entity_id = serializers.IntegerField(read_only=True)
    entity_name = serializers.CharField(source="entity.name", read_only=True)
    entity_type = serializers.CharField(source="entity.entity_type", read_only=True)
    source_id = serializers.CharField(source="entity.source_id", read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "entity_id",
            "entity_name",
            "entity_type",
            "source_id",
            "match_type",
            "confidence",
            "explanation",
            "resolved",
            "resolution",
            "created_at",
        ]
        read_only_fields = fields


class ScreeningCaseSerializer(serializers.ModelSerializer):
    """List representation: the case without its matches."""

    agent_name = serializers.CharField(source="agent.name", read_only=True)
    match_count = serializers.IntegerField(source="matches.count", read_only=True)

    class Meta:
        model = ScreeningCase
        fields = [
            "id",
            "agent_id",
            "agent_name",
            "risk_score",
            "status",
            "match_count",
            "created_at",
        ]
        read_only_fields = fields


class ScreeningCaseDetailSerializer(serializers.ModelSerializer):
    """Detail representation: the case, its agent, and every match."""

    agent = AgentSerializer(read_only=True)
    matches = MatchSerializer(many=True, read_only=True)

    class Meta:
        model = ScreeningCase
        fields = [
            "id",
            "agent",
            "risk_score",
            "status",
            "matches",
            "network_snapshot",
            "created_at",
        ]
        read_only_fields = fields


class ScreenRequestSerializer(serializers.Serializer):
    """Input for POST /api/screen/."""

    agent_id = serializers.IntegerField()
    identifiers = serializers.ListField(required=False, default=list)

    def validate_agent_id(self, value):
        if not Agent.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"No agent with id {value}.")
        return value

    def validate_identifiers(self, value):
        """Normalise [id_type, raw_value] pairs; JSON turns tuples into lists."""
        pairs = []
        for item in value:
            if isinstance(item, dict):
                id_type = item.get("id_type")
                raw_value = item.get("value") or item.get("raw_value")
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                id_type, raw_value = item
            else:
                raise serializers.ValidationError(
                    "Each identifier must be an [id_type, value] pair."
                )

            if not raw_value:
                raise serializers.ValidationError("Identifier value cannot be empty.")
            pairs.append((id_type, str(raw_value)))
        return pairs
