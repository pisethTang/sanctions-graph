import { computed, ref, toValue } from "vue";
import type { MaybeRef } from "vue";
import type { Match } from "../types/api";

export interface MatchFilters {
  matchType: string;
  entityType: string;
  minConfidence: number;
}

export function useMatchFilters(matches: MaybeRef<Match[]>) {
  const filters = ref<MatchFilters>({
    matchType: "",
    entityType: "",
    minConfidence: 0,
  });

  const filtered = computed(() => {
    const source = toValue(matches);
    let result = source;

    if (filters.value.matchType) {
      result = result.filter((m) => m.match_type === filters.value.matchType);
    }

    if (filters.value.entityType) {
      result = result.filter((m) => m.entity_type === filters.value.entityType);
    }

    if (filters.value.minConfidence > 0) {
      result = result.filter(
        (m) => m.confidence >= filters.value.minConfidence
      );
    }

    return [...result].sort((a, b) => b.confidence - a.confidence);
  });

  function resetFilters() {
    filters.value = {
      matchType: "",
      entityType: "",
      minConfidence: 0,
    };
  }

  return { filters, filtered, resetFilters };
}
