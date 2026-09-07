"""API endpoints for creating agents, screening them, and reading cases."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from screening.matcher import ScreenMatcher
from screening.models import (
    Agent,
    EntityAddress,
    EntityIdentifier,
    Match,
    ScreeningCase,
)
from screening.serializers import (
    AgentSerializer,
    MatchSerializer,
    ScreeningCaseDetailSerializer,
    ScreeningCaseSerializer,
    ScreenRequestSerializer,
)


def build_network(case):
    """Cytoscape elements for one case: the agent, its hits, and their links.

    Node ids are namespaced ("agent-3" / "entity-7") so an agent pk can never
    collide with an entity pk.
    """
    agent = case.agent
    agent_node = f"agent-{agent.pk}"

    nodes = [
        {
            "data": {
                "id": agent_node,
                "label": agent.name,
                "type": "agent",
                "risk_score": case.risk_score,
            }
        }
    ]
    edges = []

    matches = list(case.matches.select_related("entity"))
    entity_ids = [m.entity_id for m in matches]

    for match in matches:
        entity = match.entity
        node_id = f"entity-{entity.pk}"
        nodes.append(
            {
                "data": {
                    "id": node_id,
                    "label": entity.name,
                    "type": entity.entity_type,
                    "risk_score": match.confidence,
                }
            }
        )
        edges.append(
            {
                "data": {
                    "source": agent_node,
                    "target": node_id,
                    "label": match.match_type,
                }
            }
        )

    # Entity-to-entity links: the shared attributes that explain a hit.
    for model, field, label in (
        (EntityAddress, "full_text", "shared_address"),
        (EntityIdentifier, "value_hash", "shared_identifier"),
    ):
        groups = {}
        rows = (
            model.objects.filter(entity_id__in=entity_ids)
            .exclude(**{field: ""})
            .values_list("entity_id", field)
        )
        for entity_id, key in rows:
            groups.setdefault(key, set()).add(entity_id)

        for members in groups.values():
            members = sorted(members)
            for i, left in enumerate(members):
                for right in members[i + 1:]:
                    edges.append(
                        {
                            "data": {
                                "source": f"entity-{left}",
                                "target": f"entity-{right}",
                                "label": label,
                            }
                        }
                    )

    return {"nodes": nodes, "edges": edges}


class AgentViewSet(ModelViewSet):
    """CRUD for the subjects being screened."""

    queryset = Agent.objects.all().order_by("-created_at")
    serializer_class = AgentSerializer
    authentication_classes = []
    permission_classes = []


class ScreenView(APIView):
    """POST /api/screen/ — run the matcher and persist the result."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        request_serializer = ScreenRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        agent = get_object_or_404(Agent, pk=data["agent_id"])
        results = ScreenMatcher().screen(agent, identifiers=data["identifiers"])

        with transaction.atomic():
            case = ScreeningCase.objects.create(
                agent=agent,
                # The strongest single hit stands in as the case risk score.
                risk_score=max((r["confidence"] for r in results), default=0),
            )
            matches = Match.objects.bulk_create(
                [
                    Match(
                        case=case,
                        entity_id=result["entity_id"],
                        match_type=result["match_type"],
                        confidence=result["confidence"],
                        explanation=result.get("explanation", ""),
                    )
                    for result in results
                ]
            )
            # network_snapshot freezes the graph as it was at run time, so the
            # decision stays auditable after the sanctions data refreshes.
            case.network_snapshot = build_network(case)
            case.save(update_fields=["network_snapshot"])

        ordered = case.matches.select_related("entity").order_by("-confidence", "id")
        return Response(
            {
                "case": ScreeningCaseSerializer(case).data,
                "matches": MatchSerializer(ordered, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ScreeningCaseViewSet(ReadOnlyModelViewSet):
    """List, retrieve, and graph the screening cases."""

    queryset = ScreeningCase.objects.select_related("agent").order_by("-created_at")
    authentication_classes = []
    permission_classes = []

    def get_serializer_class(self):
        if self.action == "list":
            return ScreeningCaseSerializer
        return ScreeningCaseDetailSerializer

    @action(detail=True, methods=["get"])
    def network(self, request, pk=None):
        """Cytoscape-compatible graph for one case."""
        case = self.get_object()
        # Prefer the snapshot taken at screening time; fall back to a live
        # rebuild for cases written before snapshots existed.
        snapshot = case.network_snapshot or {}
        if not snapshot.get("nodes"):
            snapshot = build_network(case)
        return Response(snapshot)
