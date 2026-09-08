import { computed, toValue } from "vue";
import type { MaybeRef } from "vue";
import type { Match } from "../types/api";

const TIER_ORDER = [
  "identifier_exact",
  "name_exact",
  "name_fuzzy",
  "address_fuzzy",
  "network_2nd_degree",
];

export function useRiskSummary(matches: MaybeRef<Match[]>) {
  const source = computed(() => toValue(matches));

  const uniqueEntityCount = computed(
    () => new Set(source.value.map((m) => m.entity_id)).size
  );

  const highestConfidence = computed(() =>
    source.value.length ? Math.max(...source.value.map((m) => m.confidence)) : 0
  );

  const matchTypeCounts = computed(() => {
    return source.value.reduce<Record<string, number>>((counts, match) => {
      counts[match.match_type] = (counts[match.match_type] || 0) + 1;
      return counts;
    }, {});
  });

  const topEntities = computed(() => {
    const bestByEntity = new Map<number, Match>();
    for (const match of source.value) {
      const current = bestByEntity.get(match.entity_id);
      if (!current || match.confidence > current.confidence) {
        bestByEntity.set(match.entity_id, match);
      }
    }
    return Array.from(bestByEntity.values())
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 3);
  });

  const strongestTier = computed(() => {
    // Lower index in TIER_ORDER means a stronger evidence tier.
    let bestIndex = TIER_ORDER.length;
    for (const match of source.value) {
      const index = TIER_ORDER.indexOf(match.match_type);
      if (index >= 0 && index < bestIndex) {
        bestIndex = index;
      }
    }
    return bestIndex < TIER_ORDER.length ? TIER_ORDER[bestIndex] : "";
  });

  return {
    uniqueEntityCount,
    highestConfidence,
    matchTypeCounts,
    topEntities,
    strongestTier,
  };
}
