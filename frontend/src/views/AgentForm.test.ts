import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import AgentForm from "./AgentForm.vue";

describe("AgentForm", () => {
  it("renders a name input field", () => {
    const wrapper = mount(AgentForm);
    expect(wrapper.find('input[name="name"]').exists()).toBe(true);
  });

  it("renders a nationality input field", () => {
    const wrapper = mount(AgentForm);
    expect(wrapper.find('input[name="nationality"]').exists()).toBe(true);
  });

  it("has a submit button", () => {
    const wrapper = mount(AgentForm);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it("displays a result section after submission", async () => {
    const wrapper = mount(AgentForm);
    await wrapper.find("form").trigger("submit");
    expect(wrapper.find(".results").exists()).toBe(true);
  });

  it("warns when a broad address is entered", async () => {
    const wrapper = mount(AgentForm);
    await wrapper.find('textarea[name="addresses"]').setValue('["Hong Kong"]');
    await wrapper.vm.$nextTick();
    expect(wrapper.find(".address-warnings").exists()).toBe(true);
    expect(wrapper.text()).toContain("very broad");
  });

  it("does not warn when a specific address is entered", async () => {
    const wrapper = mount(AgentForm);
    await wrapper
      .find('textarea[name="addresses"]')
      .setValue('["Suite 1201, 88 Collyer Quay, Singapore 049320"]');
    await wrapper.vm.$nextTick();
    expect(wrapper.find(".address-warnings").exists()).toBe(false);
  });
});