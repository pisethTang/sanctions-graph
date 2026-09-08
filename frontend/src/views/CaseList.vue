<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getCases } from "../services/api";
import type { ScreeningCase } from "../types/api";

// useRouter() is inject()-based: it is undefined when this component is
// mounted without the router plugin, so every use of it is optional-chained.
const router = useRouter();

const cases = ref<ScreeningCase[]>([]);
const loading = ref(false);
const error = ref("");

function open(id: number) {
  router?.push(`/cases/${id}`);
}

onMounted(async () => {
  loading.value = true;
  try {
    const data = await getCases();
    // DRF returns a bare list unless pagination is switched on.
    cases.value = Array.isArray(data) ? data : (data?.results ?? []);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <section class="case-list">
    <h1>Cases</h1>

    <p v-if="loading" class="loading">Loading cases...</p>
    <p v-else-if="error" class="error">{{ error }}</p>

    <table>
      <thead>
        <tr>
          <th>Case ID</th>
          <th>Agent Name</th>
          <th>Risk Score</th>
          <th>Status</th>
          <th>Created At</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in cases" :key="row.id">
          <td>
            <a :href="`/cases/${row.id}`" @click.prevent="open(row.id)">{{ row.id }}</a>
          </td>
          <td>{{ row.agent_name }}</td>
          <td>{{ row.risk_score }}</td>
          <td>{{ row.status }}</td>
          <td>{{ new Date(row.created_at).toLocaleString() }}</td>
        </tr>
        <tr v-if="!cases.length && !loading">
          <td colspan="5">No cases yet.</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
th,
td {
  border-bottom: 1px solid #ddd;
  padding: 0.5rem;
  text-align: left;
}
.error {
  color: #b00020;
}
</style>
