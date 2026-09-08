<script setup lang="ts">
import { computed, ref } from "vue";
import { createAgent, screenAgent } from "../services/api";
import { useAddressQuality } from "../composables/useAddressQuality";
import type { Agent, IdentifierPair, ScreenResult } from "../types/api";

const name = ref("");
const nationality = ref("");
const aliases = ref("");
const addresses = ref("[]");
const identifiers = ref("[]");

// `submitted` gates the results panel and is set before any await, so the
// panel is on screen while the request is still in flight.
const submitted = ref(false);
const loading = ref(false);
const error = ref("");
const result = ref<ScreenResult | null>(null);

/** Parse a textarea holding a JSON array; blank counts as an empty array. */
function parseJsonArray(raw: string, field: string): unknown[] {
  const trimmed = raw.trim();
  if (!trimmed) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error(`${field} is not valid JSON.`);
  }
  if (!Array.isArray(parsed)) throw new Error(`${field} must be a JSON array.`);
  return parsed;
}

/** Extract full_text values from the address JSON array. */
function parseAddressTexts(raw: string): string[] {
  try {
    const parsed = parseJsonArray(raw, "Addresses");
    return parsed
      .map((item) =>
        typeof item === "string"
          ? item
          : (item as Record<string, string>)?.full_text || ""
      )
      .filter(Boolean) as string[];
  } catch {
    return [];
  }
}

const addressWarnings = computed(() => {
  return parseAddressTexts(addresses.value)
    .map((text) => ({ text, ...useAddressQuality(text) }))
    .filter((item) => item.isBroad.value);
});

async function onSubmit() {
  submitted.value = true;
  loading.value = true;
  error.value = "";
  result.value = null;

  try {
    const agentPayload = {
      name: name.value.trim(),
      nationality: nationality.value.trim(),
      aliases: aliases.value
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean),
      addresses: parseJsonArray(addresses.value, "Addresses") as string[],
    };
    const pairs = parseJsonArray(identifiers.value, "Identifiers") as IdentifierPair[];

    const agent: Agent = await createAgent(agentPayload);
    result.value = await screenAgent(agent.id, pairs);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="agent-form">
    <h1>New Screening</h1>

    <form @submit.prevent="onSubmit">
      <label>
        Name
        <input name="name" v-model="name" type="text" placeholder="Full name" />
      </label>

      <label>
        Nationality (2-letter)
        <input
          name="nationality"
          v-model="nationality"
          type="text"
          maxlength="2"
          placeholder="ru"
        />
      </label>

      <label>
        Aliases (comma-separated)
        <input name="aliases" v-model="aliases" type="text" placeholder="Vova, V. Putin" />
      </label>

      <label>
        Addresses (JSON array)
        <textarea name="addresses" v-model="addresses" rows="3"></textarea>
      </label>
      <ul v-if="addressWarnings.length" class="address-warnings">
        <li v-for="(item, index) in addressWarnings" :key="index">
          <strong>Warning:</strong> {{ item.warning.value }}
          <span class="address-preview">("{{ item.text }}")</span>
        </li>
      </ul>

      <label>
        Identifiers (JSON array of [type, value])
        <textarea name="identifiers" v-model="identifiers" rows="3"></textarea>
      </label>

      <button type="submit" :disabled="loading">
        {{ loading ? "Screening..." : "Screen agent" }}
      </button>
    </form>

    <div v-if="submitted" class="results">
      <p v-if="loading" class="loading">Running the matcher...</p>
      <p v-else-if="error" class="error">{{ error }}</p>
      <dl v-else-if="result">
        <dt>Case ID</dt>
        <dd>{{ result.case.id }}</dd>
        <dt>Matches</dt>
        <dd>{{ result.matches.length }}</dd>
        <dt>Highest confidence</dt>
        <dd>{{ result.matches.length ? result.matches[0].confidence : 0 }}</dd>
      </dl>
      <p v-else class="empty">No result.</p>
    </div>
  </section>
</template>

<style scoped>
.agent-form {
  max-width: 40rem;
  margin: 0 auto;
}
form {
  display: grid;
  gap: 0.75rem;
}
label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.875rem;
}
input,
textarea {
  padding: 0.5rem;
  font: inherit;
}
button {
  justify-self: start;
  padding: 0.5rem 1rem;
}
.results {
  margin-top: 1.5rem;
  padding: 1rem;
  border: 1px solid #ccc;
}
.results dl {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.25rem 1rem;
  margin: 0;
}
.results dt {
  font-weight: 600;
}
.error {
  color: #b00020;
}
.address-warnings {
  list-style: none;
  margin: -0.5rem 0 0.5rem;
  padding: 0.5rem;
  background: #fff3e0;
  border: 1px solid #ffb74d;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #e65100;
}
.address-warnings li {
  margin-bottom: 0.25rem;
}
.address-warnings li:last-child {
  margin-bottom: 0;
}
.address-preview {
  color: #bf360c;
}
</style>
