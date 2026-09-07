import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import CaseDetail from "./CaseDetail.vue";

describe("CaseDetail", () => {
  it("renders a match list panel", () => {
    const wrapper = mount(CaseDetail, {
      global: { mocks: { $route: { params: { id: "1" } } } },
    });
    expect(wrapper.find(".match-list").exists()).toBe(true);
  });

  it("renders a graph container", () => {
    const wrapper = mount(CaseDetail, {
      global: { mocks: { $route: { params: { id: "1" } } } },
    });
    expect(wrapper.find(".graph-container").exists()).toBe(true);
  });
});