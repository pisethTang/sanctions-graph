import { describe, it, expect } from "vitest";

// The composable will be implemented next. Import it lazily so the tests fail
// cleanly with a useful message if it is missing.
function loadComposable() {
  try {
    return import("./useMatchFilters");
  } catch (err) {
    throw new Error(
      "useMatchFilters.ts does not exist yet. Create it before running these tests."
    );
  }
}

// Sample matches mirror the DRF MatchSerializer shape.
const sampleMatches = [
  {
    id: 1,
    entity_id: 101,
    entity_name: "Sergei Lavrov",
    entity_type: "person",
    source_id: "NK-demo-pep",
    match_type: "name_exact",
    confidence: 95,
    explanation: "Name matches sanctioned record 'Sergei Lavrov'",
    resolved: false,
    resolution: "",
    created_at: "2026-09-08T10:00:00Z",
  },
  {
    id: 2,
    entity_id: 102,
    entity_name: "Wong & Associates Pte Ltd",
    entity_type: "organization",
    source_id: "NK-demo-hub",
    match_type: "address_fuzzy",
    confidence: 100,
    explanation: "Address is a 100% trigram match",
    resolved: false,
    resolution: "",
    created_at: "2026-09-08T10:00:00Z",
  },
  {
    id: 3,
    entity_id: 103,
    entity_name: "Li Wei",
    entity_type: "person",
    source_id: "NK-demo-person-a",
    match_type: "address_fuzzy",
    confidence: 100,
    explanation: "Address is a 100% trigram match",
    resolved: false,
    resolution: "",
    created_at: "2026-09-08T10:00:00Z",
  },
  {
    id: 4,
    entity_id: 104,
    entity_name: "NAYARA ENERGY SINGAPORE PTE. LIMITED",
    entity_type: "organization",
    source_id: "NK-real-001",
    match_type: "address_fuzzy",
    confidence: 53,
    explanation: "Address is a 53% trigram match",
    resolved: false,
    resolution: "",
    created_at: "2026-09-08T10:00:00Z",
  },
];

describe("useMatchFilters", () => {
  it("returns all matches when no filter is active", async () => {
    const { useMatchFilters } = await loadComposable();
    const { filtered } = useMatchFilters(sampleMatches);
    expect(filtered.value).toHaveLength(sampleMatches.length);
  });

  it("filters by match_type", async () => {
    const { useMatchFilters } = await loadComposable();
    const { filters, filtered } = useMatchFilters(sampleMatches);
    filters.value.matchType = "address_fuzzy";
    expect(filtered.value.every((m) => m.match_type === "address_fuzzy")).toBe(true);
    expect(filtered.value).toHaveLength(3);
  });

  it("filters by entity_type", async () => {
    const { useMatchFilters } = await loadComposable();
    const { filters, filtered } = useMatchFilters(sampleMatches);
    filters.value.entityType = "person";
    expect(filtered.value.every((m) => m.entity_type === "person")).toBe(true);
    expect(filtered.value).toHaveLength(2);
  });

  it("filters by minimum confidence", async () => {
    const { useMatchFilters } = await loadComposable();
    const { filters, filtered } = useMatchFilters(sampleMatches);
    filters.value.minConfidence = 80;
    expect(filtered.value.every((m) => m.confidence >= 80)).toBe(true);
    expect(filtered.value).toHaveLength(3);
  });

  it("combines multiple filters", async () => {
    const { useMatchFilters } = await loadComposable();
    const { filters, filtered } = useMatchFilters(sampleMatches);
    filters.value.matchType = "address_fuzzy";
    filters.value.entityType = "organization";
    filters.value.minConfidence = 80;
    expect(filtered.value).toHaveLength(1);
    expect(filtered.value[0].entity_name).toBe("Wong & Associates Pte Ltd");
  });

  it("resetFilters clears all active filters", async () => {
    const { useMatchFilters } = await loadComposable();
    const { filters, filtered, resetFilters } = useMatchFilters(sampleMatches);
    filters.value.matchType = "address_fuzzy";
    filters.value.minConfidence = 80;
    resetFilters();
    expect(filtered.value).toHaveLength(sampleMatches.length);
    expect(filters.value.matchType).toBe("");
    expect(filters.value.minConfidence).toBe(0);
  });

  it("provides a sorted list by confidence descending", async () => {
    const { useMatchFilters } = await loadComposable();
    const { filtered } = useMatchFilters(sampleMatches);
    const confidences = filtered.value.map((m) => m.confidence);
    expect(confidences).toEqual([...confidences].sort((a, b) => b - a));
  });
});
