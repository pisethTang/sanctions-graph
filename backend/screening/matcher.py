"""Screen an agent against the sanctions tables and explain every hit.

The pipeline runs the evidence tiers in `Match.MATCH_TYPES` order, strongest
first. An entity that matches at one tier is not reconsidered by a weaker one,
so a name that also happens to be a perfect trigram match is still reported as
the exact match it is.
"""

import networkx as nx
from django.db import connection

from screening.models import (
    EntityAddress,
    EntityAlias,
    EntityIdentifier,
    SanctionedEntity,
)

# Trigram cut-offs. These are deliberately below the "obvious" 0.7/0.6: the
# real pg_trgm score for a one-letter surname typo is 0.667, and for
# "Moscow, Russia" vs "Moscow, Russian Federation" it is 0.481, so higher
# thresholds silently match nothing. See test_matcher.py for the fixtures.
NAME_FUZZY_THRESHOLD = 0.6
ADDRESS_FUZZY_THRESHOLD = 0.4

# Pipeline order, used to decide which tier wins when one entity hits twice.
TIER_ORDER = [
    "identifier_exact",
    "name_exact",
    "name_fuzzy",
    "address_fuzzy",
    "network_2nd_degree",
]

NETWORK_CONFIDENCE = 50


class ScreenMatcher:
    """Runs the screening tiers and returns deduplicated, ranked matches."""

    def __init__(
        self,
        name_threshold=NAME_FUZZY_THRESHOLD,
        address_threshold=ADDRESS_FUZZY_THRESHOLD,
    ):
        self.name_threshold = name_threshold
        self.address_threshold = address_threshold

    def screen(self, agent, identifiers=None):
        """Screen `agent`, optionally with a list of (id_type, raw_value) tuples."""
        identifiers = identifiers or []
        agent_addresses = self._agent_addresses(agent)

        # entity_id -> match dict, best tier wins.
        found = {}

        identifier_hashes = self._identifier_hashes(identifiers)
        self._collect(found, self._identifier_matches(identifier_hashes))
        self._collect(found, self._name_exact_matches(agent))
        self._collect(found, self._name_fuzzy_matches(agent))

        address_hits = self._address_fuzzy_matches(agent_addresses)
        self._collect(found, address_hits)

        # Entities directly linked to the agent seed the network walk.
        seed_ids = {hit["entity_id"] for hit in address_hits}
        seed_ids.update(
            EntityIdentifier.objects.filter(
                value_hash__in=identifier_hashes
            ).values_list("entity_id", flat=True)
        )
        self._collect(found, self._network_matches(agent, seed_ids))

        return sorted(found.values(), key=lambda m: m["confidence"], reverse=True)

    # ------------------------------------------------------------------ tiers

    def _identifier_matches(self, identifier_hashes):
        if not identifier_hashes:
            return []

        rows = EntityIdentifier.objects.filter(
            value_hash__in=identifier_hashes
        ).values_list("entity_id", "id_type")

        return [
            {
                "entity_id": entity_id,
                "match_type": "identifier_exact",
                "confidence": 100,
                "explanation": "Exact identifier match",
            }
            for entity_id, id_type in rows
        ]

    def _name_exact_matches(self, agent):
        """Case-insensitive hits on the entity's own name or any of its aliases."""
        names = [agent.name] + [a for a in (agent.aliases or []) if a]

        matches = []
        for name in names:
            if not str(name).strip():
                continue

            for entity_id in SanctionedEntity.objects.filter(
                name__iexact=name
            ).values_list("id", flat=True):
                matches.append(self._name_exact(entity_id, name))

            for entity_id, text in EntityAlias.objects.filter(
                text__iexact=name
            ).values_list("entity_id", "text"):
                matches.append(self._name_exact(entity_id, text))

        return matches

    @staticmethod
    def _name_exact(entity_id, name):
        return {
            "entity_id": entity_id,
            "match_type": "name_exact",
            "confidence": 95,
            "explanation": f"Name matches sanctioned record '{name}'",
        }

    def _name_fuzzy_matches(self, agent):
        """Trigram search over both entity names and aliases."""
        names = [agent.name] + [a for a in (agent.aliases or []) if a]

        sql = """
            SELECT entity_id, MAX(score) AS score FROM (
                SELECT entity_id, similarity(text, %s) AS score
                FROM screening_entityalias
                WHERE similarity(text, %s) > %s
                UNION ALL
                SELECT id AS entity_id, similarity(name, %s) AS score
                FROM screening_sanctionedentity
                WHERE similarity(name, %s) > %s
            ) hits
            GROUP BY entity_id
        """

        matches = []
        for name in names:
            if not str(name).strip():
                continue
            params = [
                name, name, self.name_threshold,
                name, name, self.name_threshold,
            ]
            for entity_id, score in self._query(sql, params):
                matches.append(
                    {
                        "entity_id": entity_id,
                        "match_type": "name_fuzzy",
                        "confidence": int(score * 100),
                        "explanation": (
                            f"Name '{name}' is a {score:.0%} trigram match "
                            f"to a sanctioned record"
                        ),
                    }
                )
        return matches

    def _address_fuzzy_matches(self, agent_addresses):
        sql = """
            SELECT entity_id, MAX(similarity(full_text, %s)) AS score
            FROM screening_entityaddress
            WHERE similarity(full_text, %s) > %s
            GROUP BY entity_id
        """

        matches = []
        for address in agent_addresses:
            if not address:
                continue
            params = [address, address, self.address_threshold]
            for entity_id, score in self._query(sql, params):
                matches.append(
                    {
                        "entity_id": entity_id,
                        "match_type": "address_fuzzy",
                        "confidence": int(score * 100),
                        "explanation": (
                            f"Address '{address}' is a {score:.0%} trigram match "
                            f"to a sanctioned record's address"
                        ),
                    }
                )
        return matches

    def _network_matches(self, agent, seed_ids):
        """Entities exactly two hops from the agent through shared attributes."""
        if not seed_ids:
            return []

        graph = nx.Graph()
        agent_node = ("agent", agent.pk)

        for entity_id in seed_ids:
            graph.add_edge(agent_node, entity_id)

        # Expand two levels out from the seeds, linking entities that share an
        # address string or an identifier hash.
        frontier = set(seed_ids)
        seen = set(seed_ids)
        for _ in range(2):
            neighbours = self._shared_attribute_edges(frontier, graph)
            frontier = neighbours - seen
            seen |= neighbours
            if not frontier:
                break

        distances = nx.single_source_shortest_path_length(
            graph, agent_node, cutoff=2
        )

        return [
            {
                "entity_id": node,
                "match_type": "network_2nd_degree",
                "confidence": NETWORK_CONFIDENCE,
                "explanation": (
                    "Linked to the agent through a shared address or identifier "
                    "at two degrees of separation"
                ),
            }
            for node, distance in distances.items()
            if distance == 2 and node != agent_node
        ]

    def _shared_attribute_edges(self, entity_ids, graph):
        """Add edges between entities sharing an address or identifier."""
        if not entity_ids:
            return set()

        reached = set()
        for model, field in (
            (EntityAddress, "full_text"),
            (EntityIdentifier, "value_hash"),
        ):
            keys = set(
                model.objects.filter(entity_id__in=entity_ids)
                .exclude(**{field: ""})
                .values_list(field, flat=True)
            )
            if not keys:
                continue

            groups = {}
            for entity_id, key in model.objects.filter(
                **{f"{field}__in": keys}
            ).values_list("entity_id", field):
                groups.setdefault(key, set()).add(entity_id)

            for members in groups.values():
                members = sorted(members)
                for i, left in enumerate(members):
                    for right in members[i + 1:]:
                        graph.add_edge(left, right)
                reached.update(members)

        return reached

    # ------------------------------------------------------------------ utils

    @staticmethod
    def _agent_addresses(agent):
        """Agent.addresses is a JSON list of dicts; tolerate plain strings too."""
        raw = getattr(agent, "addresses", []) or []
        addresses = []
        for item in raw:
            if isinstance(item, dict):
                text = item.get("full_text") or ""
            else:
                text = str(item)
            text = text.strip()
            if text:
                addresses.append(text)
        return addresses

    @staticmethod
    def _identifier_hashes(identifiers):
        return [
            EntityIdentifier.hash_value(raw_value)
            for _id_type, raw_value in identifiers
            if raw_value and str(raw_value).strip()
        ]

    @staticmethod
    def _query(sql, params):
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    @staticmethod
    def _collect(found, matches):
        """Keep the strongest tier per entity, then the highest confidence."""
        for match in matches:
            entity_id = match["entity_id"]
            current = found.get(entity_id)
            if current is None:
                found[entity_id] = match
                continue

            new_rank = TIER_ORDER.index(match["match_type"])
            current_rank = TIER_ORDER.index(current["match_type"])
            if (new_rank, -match["confidence"]) < (current_rank, -current["confidence"]):
                found[entity_id] = match
