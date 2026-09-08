import { describe, it, expect, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import CaseDetail from "./CaseDetail.vue";

vi.mock("../services/api", () => ({
  getCase: vi.fn(() =>
    Promise.resolve({
      id: 1,
      agent: {
        id: 1,
        name: "Test Agent",
        nationality: "ru",
        aliases: [],
        addresses: [],
        created_at: "2026-09-08T10:00:00Z",
      },
      risk_score: 95,
      status: "open",
      matches: [
        {
          id: 1,
          entity_id: 101,
          entity_name: "Sergei Lavrov",
          entity_type: "person",
          source_id: "NK-demo-pep",
          is_target: true,
          match_type: "name_exact",
          confidence: 95,
          explanation: "Name matches sanctioned record",
          resolved: false,
          resolution: "",
          created_at: "2026-09-08T10:00:00Z",
        },
      ],
      network_snapshot: null,
      created_at: "2026-09-08T10:00:00Z",
    })
  ),
  getNetwork: vi.fn(() =>
    Promise.resolve({
      nodes: [{ data: { id: "agent-1", label: "Test Agent", type: "agent", risk_score: 95 } }],
      edges: [],
    })
  ),
  updateMatchResolution: vi.fn((id: number, resolved: boolean, resolution: string) =>
    Promise.resolve({
      id,
      entity_id: 101,
      entity_name: "Sergei Lavrov",
      entity_type: "person",
      source_id: "NK-demo-pep",
      is_target: true,
      match_type: "name_exact",
      confidence: 95,
      explanation: "Name matches sanctioned record",
      resolved,
      resolution,
      created_at: "2026-09-08T10:00:00Z",
    })
  ),
}));

describe("CaseDetail", () => {
  it("renders a match list panel", () => {
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });
    expect(wrapper.find(".match-list").exists()).toBe(true);
  });

  it("renders a graph container", () => {
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });
    expect(wrapper.find(".graph-container").exists()).toBe(true);
  });

  it("renders match cards after the API data loads", async () => {
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });

    await flushPromises();

    // The summary should reflect the loaded matches, not the initial empty state.
    expect(wrapper.text()).toContain("1 matched entity");
    expect(wrapper.text()).toContain("Sergei Lavrov");
    expect(wrapper.find(".entity-card").exists()).toBe(true);
  });

  it("shows strongest evidence and match counts in the summary bar", async () => {
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });

    await flushPromises();

    expect(wrapper.text()).toContain("Strongest evidence");
    expect(wrapper.text()).toContain("name_exact");
    expect(wrapper.text()).toContain("name_exact");
  });

  it("renders a graph legend explaining node and edge colors", async () => {
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });

    await flushPromises();

    const legend = wrapper.find(".graph-legend");
    expect(legend.exists()).toBe(true);
    expect(legend.text()).toContain("Your agent");
    expect(legend.text()).toContain("Person");
    expect(legend.text()).toContain("Organization");
    expect(legend.text()).toContain("Confirmed hit");
    expect(legend.text()).toContain("Dismissed");
    expect(legend.text()).toContain("Agent matches");
    expect(legend.text()).toContain("Name match");
    expect(legend.text()).toContain("Identifier / address match");
    expect(legend.text()).toContain("Entity links");
    expect(legend.text()).toContain("Shared address / identifier");
  });

  it("marks an entity card as selected when clicked", async () => {
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });

    await flushPromises();
    const card = wrapper.find(".entity-card");
    expect(card.classes()).not.toContain("selected");

    await card.trigger("click");
    expect(card.classes()).toContain("selected");
  });

  it("marks a match as a false positive from the card actions", async () => {
    const { updateMatchResolution } = await import("../services/api");
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });

    await flushPromises();
    await wrapper.find(".card-actions .dismiss").trigger("click");
    await flushPromises();

    expect(updateMatchResolution).toHaveBeenCalledWith(1, true, "false_positive");
    expect(wrapper.find(".resolution-badge").text()).toBe("False positive");
    expect(wrapper.find(".entity-card").classes()).toContain("resolved");
  });

  it("reopens a resolved match", async () => {
    const { updateMatchResolution } = await import("../services/api");
    const wrapper = mount(CaseDetail, {
      props: { caseId: 1 },
      global: { mocks: { $route: { params: { id: "1" } } } },
    });

    await flushPromises();
    await wrapper.find(".card-actions .confirm").trigger("click");
    await flushPromises();
    expect(wrapper.find(".resolution-badge").text()).toBe("Confirmed hit");

    await wrapper.find(".card-actions .reopen").trigger("click");
    await flushPromises();

    expect(updateMatchResolution).toHaveBeenLastCalledWith(1, false, "");
    expect(wrapper.find(".resolution-badge").exists()).toBe(false);
  });
});
