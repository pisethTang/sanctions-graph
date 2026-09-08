import { describe, it, expect } from "vitest";

function loadComposable() {
  try {
    return import("./useAddressQuality");
  } catch (err) {
    throw new Error(
      "useAddressQuality.ts does not exist yet. Create it before running these tests."
    );
  }
}

describe("useAddressQuality", () => {
  it("flags a country-only address as broad", async () => {
    const { useAddressQuality } = await loadComposable();
    const result = useAddressQuality("Hong Kong");
    expect(result.isBroad.value).toBe(true);
    expect(result.score.value).toBeLessThan(0.5);
    expect(result.warning.value).toBeTruthy();
  });

  it("flags a city-only address as broad", async () => {
    const { useAddressQuality } = await loadComposable();
    const result = useAddressQuality("Moscow");
    expect(result.isBroad.value).toBe(true);
    expect(result.warning.value).toBeTruthy();
  });

  it("does not flag a street address as broad", async () => {
    const { useAddressQuality } = await loadComposable();
    const result = useAddressQuality(
      "Suite 1201, 88 Collyer Quay, Singapore 049320"
    );
    expect(result.isBroad.value).toBe(false);
    expect(result.score.value).toBeGreaterThanOrEqual(0.7);
    expect(result.warning.value).toBe("");
  });

  it("normalises whitespace and case", async () => {
    const { useAddressQuality } = await loadComposable();
    const r1 = useAddressQuality("  hong kong  ");
    const r2 = useAddressQuality("HONG KONG");
    expect(r1.isBroad.value).toBe(r2.isBroad.value);
    expect(r1.score.value).toBeCloseTo(r2.score.value, 2);
  });

  it("returns empty/valid state for an empty address", async () => {
    const { useAddressQuality } = await loadComposable();
    const result = useAddressQuality("");
    expect(result.isBroad.value).toBe(false);
    expect(result.score.value).toBe(0);
    expect(result.warning.value).toBe("");
  });

  it("warns when an address is only a country code string", async () => {
    const { useAddressQuality } = await loadComposable();
    const result = useAddressQuality("hk");
    expect(result.isBroad.value).toBe(true);
  });
});
