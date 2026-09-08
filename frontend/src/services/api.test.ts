import { describe, it, expect, vi, beforeEach } from "vitest";
import { createAgent, screenAgent, getCases, getNetwork } from "./api";

// mock testing ...
describe("API service", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("createAgent POSTs JSON and returns parsed response", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ id: 1, name: "Test Agent" }),
      } as Response)
    );

    const result = await createAgent({ name: "Test Agent", nationality: "ru" });

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/agents/",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "Test Agent", nationality: "ru" }),
      })
    );
    expect(result.id).toBe(1);
  });

  it("screenAgent sends identifiers and returns case", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ case: { id: 1 }, matches: [] }),
      } as Response)
    );

    const result = await screenAgent(1, [["passport", "X123"]]);

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/screen/",
      expect.objectContaining({ method: "POST" })
    );
    expect(result.case.id).toBe(1);
  });

  it("getCases returns list", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve([{ id: 1, risk_score: 100 }]),
      } as Response)
    );

    const result = await getCases();
    expect(Array.isArray(result)).toBe(true);
    expect(result[0].risk_score).toBe(100);
  });

  it("throws on HTTP error", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 400 } as Response)
    );

    await expect(getNetwork(1)).rejects.toThrow("HTTP 400");
  });
});