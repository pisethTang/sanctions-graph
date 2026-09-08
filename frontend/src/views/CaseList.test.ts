import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import CaseList from "./CaseList.vue";

describe("CaseList", () => {
  it("renders a table container", () => {
    const wrapper = mount(CaseList);
    expect(wrapper.find("table").exists()).toBe(true);
  });

  it("renders a cases heading", () => {
    const wrapper = mount(CaseList);
    expect(wrapper.text()).toContain("Cases");
  });
}); 