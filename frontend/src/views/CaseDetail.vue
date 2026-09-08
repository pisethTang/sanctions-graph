<script setup lang="ts">
import { computed, getCurrentInstance, onBeforeUnmount, onMounted, ref } from "vue";
import cytoscape from "cytoscape";
import type { Core } from "cytoscape";
import { getCase, getNetwork } from "../services/api";
import type { CaseDetail, Match, NetworkGraph } from "../types/api";

// Read the route off the component proxy rather than useRoute(): that keeps
// the component mountable with a plain { $route } stub and still resolves
// through the real router in the app.
const proxy = getCurrentInstance()?.proxy as
  | { $route?: { params?: Record<string, string | string[]> } }
  | undefined;
const rawId = proxy?.$route?.params?.id;
const caseId = Number(Array.isArray(rawId) ? rawId[0] : rawId);

const detail = ref<CaseDetail | null>(null);
const matches = ref<Match[]>([]);
const loading = ref(false);
const error = ref("");
const sidebarOpen = ref(true);

const graphEl = ref<HTMLElement | null>(null);
let cy: Core | null = null;

interface EntityGroup {
  entity_id: number;
  entity_name: string;
  entity_type: string;
  source_id: string;
  matches: Match[];
  bestConfidence: number;
}

const groupedMatches = computed<EntityGroup[]>(() => {
  const map = new Map<number, EntityGroup>();
  for (const match of matches.value) {
    const existing = map.get(match.entity_id);
    if (existing) {
      existing.matches.push(match);
      existing.bestConfidence = Math.max(existing.bestConfidence, match.confidence);
    } else {
      map.set(match.entity_id, {
        entity_id: match.entity_id,
        entity_name: match.entity_name,
        entity_type: match.entity_type,
        source_id: match.source_id,
        matches: [match],
        bestConfidence: match.confidence,
      });
    }
  }
  return Array.from(map.values()).sort((a, b) => b.bestConfidence - a.bestConfidence);
});

const uniqueEntityCount = computed(() => groupedMatches.value.length);

function fitGraph() {
  cy?.fit(undefined, 24);
}

function renderGraph(graph: NetworkGraph) {
  if (!graphEl.value) return;
  try {
    cy?.destroy();
    cy = cytoscape({
      container: graphEl.value,
      elements: [...(graph.nodes ?? []), ...(graph.edges ?? [])],
      layout: {
        name: "cose",
        animate: false,
        componentSpacing: 80,
        nodeOverlap: 20,
        idealEdgeLength: 60,
        nodeRepulsion: 800000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 40,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      },
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": "10px",
            "background-color": "#607d8b",
            width: "mapData(degree, 1, 20, 16, 48)",
            height: "mapData(degree, 1, 20, 16, 48)",
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 4,
            "text-background-color": "#fff",
            "text-background-opacity": 0.85,
            "text-background-padding": "2px",
            color: "#333",
          },
        },
        {
          selector: 'node[type = "agent"]',
          style: {
            "background-color": "#1976d2",
            width: 48,
            height: 48,
            "font-size": "12px",
            "font-weight": "bold",
            "z-index": 999,
          },
        },
        {
          selector: 'node[type = "person"]',
          style: { "background-color": "#d84315" },
        },
        {
          selector: 'node[type = "organization"]',
          style: { "background-color": "#2e7d32" },
        },
        {
          selector: "edge",
          style: {
            "curve-style": "bezier",
            "line-color": "#bbb",
            "target-arrow-shape": "triangle",
            "target-arrow-color": "#bbb",
            width: 1.5,
          },
        },
        {
          selector: "edge[label *= 'shared']",
          style: { "line-color": "#f57c00", "target-arrow-color": "#f57c00" },
        },
        {
          selector: "edge[label *= 'name']",
          style: { "line-color": "#1976d2", "target-arrow-color": "#1976d2" },
        },
        {
          selector: ":selected",
          style: {
            "border-width": 3,
            "border-color": "#ffd600",
            "border-opacity": 1,
          },
        },
      ],
    });

    // Hide labels on low-degree nodes until hovered to reduce clutter.
    cy.style().selector("node[degree < 2]").style({ label: "" }).update();

    cy.on("mouseover", "node", (evt) => {
      evt.target.style("label", evt.target.data("label"));
    });
    cy.on("mouseout", "node", (evt) => {
      if ((evt.target.data("degree") ?? 0) < 2) {
        evt.target.style("label", "");
      }
    });

    cy.ready(fitGraph);
  } catch (err) {
    // jsdom and other headless containers have no layout box for cytoscape to
    // measure; the match list is still the useful half of the page.
    error.value = err instanceof Error ? err.message : String(err);
  }
}

onMounted(async () => {
  if (!Number.isFinite(caseId) || caseId <= 0) return;
  loading.value = true;
  try {
    const [caseData, graph] = await Promise.all([getCase(caseId), getNetwork(caseId)]);
    detail.value = caseData;
    matches.value = caseData?.matches ?? [];
    renderGraph(graph);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
});

onBeforeUnmount(() => {
  cy?.destroy();
  cy = null;
});
</script>

<template>
  <section class="case-detail">
    <h1>Case {{ caseId }}</h1>
    <p v-if="loading" class="loading">Loading case...</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else-if="detail" class="summary">
      {{ detail.agent.name }} &middot; risk {{ detail.risk_score }} &middot;
      {{ detail.status }} &middot; {{ uniqueEntityCount }} matched entity<span v-if="uniqueEntityCount !== 1">ies</span>
    </p>

    <div class="panels" :class="{ 'sidebar-open': sidebarOpen }">
      <aside class="match-sidebar">
        <button
          type="button"
          class="toggle"
          @click="sidebarOpen = !sidebarOpen"
          :aria-expanded="sidebarOpen"
        >
          {{ sidebarOpen ? "Hide matches" : `Show matches (${uniqueEntityCount})` }}
        </button>

        <div v-if="sidebarOpen" class="match-list-wrap">
          <ul class="match-list">
            <li v-for="group in groupedMatches" :key="group.entity_id" class="entity-card">
              <div class="entity-header">
                <span class="entity-name" :title="group.entity_name">{{ group.entity_name }}</span>
                <span class="entity-meta">{{ group.entity_type }} &middot; {{ group.bestConfidence }}</span>
              </div>
              <div class="reasons">
                <span v-for="match in group.matches" :key="match.id" class="reason">
                  {{ match.match_type }} ({{ match.confidence }})
                </span>
              </div>
              <p class="source-id">{{ group.source_id }}</p>
            </li>
            <li v-if="!groupedMatches.length" class="empty">No matches on this case.</li>
          </ul>
        </div>
      </aside>

      <div class="graph-wrap">
        <div class="graph-toolbar">
          <button type="button" @click="fitGraph">Fit graph</button>
        </div>
        <div class="graph-container" ref="graphEl"></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.case-detail {
  container-type: inline-size;
}
.panels {
  display: grid;
  gap: 1rem;
  align-items: start;
}
.panels.sidebar-open {
  grid-template-columns: minmax(18rem, 22rem) 1fr;
}

.match-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.toggle {
  align-self: flex-start;
  padding: 0.4rem 0.75rem;
  cursor: pointer;
}
.match-list-wrap {
  max-height: 36rem;
  overflow-y: auto;
  border: 1px solid #ddd;
}
.match-list {
  list-style: none;
  margin: 0;
  padding: 0.5rem;
}
.entity-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 0.6rem;
  margin-bottom: 0.5rem;
  background: #fafafa;
}
.entity-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
}
.entity-name {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.entity-meta {
  font-size: 0.75rem;
  color: #666;
  flex-shrink: 0;
}
.reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.4rem;
}
.reason {
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
  border-radius: 999px;
  background: #e3f2fd;
  color: #0d47a1;
}
.source-id {
  margin: 0.4rem 0 0;
  font-size: 0.7rem;
  color: #888;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty {
  color: #666;
  padding: 1rem;
  text-align: center;
}

.graph-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}
.graph-toolbar {
  display: flex;
  justify-content: flex-end;
}
.graph-toolbar button {
  padding: 0.35rem 0.75rem;
  cursor: pointer;
}
.graph-container {
  height: 40rem;
  border: 1px solid #ddd;
  background: #fafafa;
}
.error {
  color: #b00020;
}

@media (max-width: 800px) {
  .panels.sidebar-open {
    grid-template-columns: 1fr;
  }
  .graph-container {
    height: 28rem;
  }
}
</style>
