"""API endpoints for creating agents, screening them, and reading cases."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from screening.matcher import ScreenMatcher
from screening.models import (
    Agent,
    EntityAddress,
    EntityIdentifier,
    Match,
    SanctionedEntity,
    ScreeningCase,
)
from screening.risk_scoring import calculate_case_risk_score
from screening.serializers import (
    AgentSerializer,
    MatchResolutionSerializer,
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
        # A 2nd-degree match is reached through a bridge entity; the shared
        # edges below carry that path, so a direct agent edge would be a lie.
        if match.match_type != "network_2nd_degree":
            category = "name" if match.match_type.startswith("name") else "identifier_address"
            edges.append(
                {
                    "data": {
                        "source": agent_node,
                        "target": node_id,
                        "label": match.match_type,
                        "category": category,
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
                for right in members[i + 1 :]:
                    edges.append(
                        {
                            "data": {
                                "source": f"entity-{left}",
                                "target": f"entity-{right}",
                                "label": label,
                                "category": "shared",
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

        # Enrich each result with the matched entity's target flag so the risk
        # scorer can distinguish direct targets from related parties.
        entity_ids = [r["entity_id"] for r in results]
        target_map = dict(
            SanctionedEntity.objects.filter(id__in=entity_ids).values_list(
                "id", "is_target"
            )
        )
        for result in results:
            result["entity"] = {"is_target": target_map.get(result["entity_id"], False)}

        with transaction.atomic():
            case = ScreeningCase.objects.create(
                agent=agent,
                # Risk score combines evidence strength, diversity, and noise.
                risk_score=calculate_case_risk_score(results),
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


class MatchViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """Review workflow for individual matches.

    PATCH /api/matches/<id>/ with {resolved, resolution}. When every match on
    a case is resolved, the case rolls up to "resolved"; reopening any match
    reopens the case.
    """

    queryset = Match.objects.select_related("case", "entity")
    authentication_classes = []
    permission_classes = []
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return MatchResolutionSerializer
        return MatchSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            match = serializer.save()
            case = match.case
            has_unresolved = case.matches.filter(resolved=False).exists()
            case.status = "open" if has_unresolved else "resolved"
            case.save(update_fields=["status"])

    def update(self, request, *args, **kwargs):
        # Officers always send partial payloads (resolved + resolution).
        kwargs["partial"] = True
        response = super().update(request, *args, **kwargs)
        # Answer with the full match representation the case page renders.
        response.data = MatchSerializer(self.get_object()).data
        return response


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
