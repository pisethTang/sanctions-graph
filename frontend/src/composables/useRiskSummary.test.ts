import { describe, it, expect } from "vitest";

function loadComposable() {
  try {
    return import("./useRiskSummary");
  } catch (err) {
    throw new Error(
      "useRiskSummary.ts does not exist yet. Create it before running these tests."
    );
  }
}

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

describe("useRiskSummary", () => {
  it("reports the total number of unique matched entities", async () => {
    const { useRiskSummary } = await loadComposable();
    const summary = useRiskSummary(sampleMatches);
    expect(summary.uniqueEntityCount.value).toBe(4);
  });

  it("reports the highest-confidence match", async () => {
    const { useRiskSummary } = await loadComposable();
    const summary = useRiskSummary(sampleMatches);
    expect(summary.highestConfidence.value).toBe(100);
  });

  it("groups match counts by type", async () => {
    const { useRiskSummary } = await loadComposable();
    const summary = useRiskSummary(sampleMatches);
    expect(summary.matchTypeCounts.value).toEqual({
      name_exact: 1,
      address_fuzzy: 3,
    });
  });

  it("lists the top 3 riskiest entities by confidence", async () => {
    const { useRiskSummary } = await loadComposable();
    const summary = useRiskSummary(sampleMatches);
    const top = summary.topEntities.value;
    expect(top).toHaveLength(3);
    expect(top[0].entity_name).toBe("Wong & Associates Pte Ltd");
    expect(top[1].entity_name).toBe("Li Wei");
    expect(top[2].entity_name).toBe("Sergei Lavrov");
  });

  it("identifies the strongest evidence tier present", async () => {
    const { useRiskSummary } = await loadComposable();
    const summary = useRiskSummary(sampleMatches);
    expect(summary.strongestTier.value).toBe("name_exact");
  });

  it("returns sensible defaults for an empty match list", async () => {
    const { useRiskSummary } = await loadComposable();
    const summary = useRiskSummary([]);
    expect(summary.uniqueEntityCount.value).toBe(0);
    expect(summary.highestConfidence.value).toBe(0);
    expect(summary.matchTypeCounts.value).toEqual({});
    expect(summary.topEntities.value).toEqual([]);
    expect(summary.strongestTier.value).toBe("");
  });
});
