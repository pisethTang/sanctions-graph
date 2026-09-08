<script setup lang="ts">
import { computed, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import cytoscape from "cytoscape";
import type { Core } from "cytoscape";
import { getCase, getNetwork, updateMatchResolution } from "../services/api";
import { useMatchFilters } from "../composables/useMatchFilters";
import { useRiskSummary } from "../composables/useRiskSummary";
import type { CaseDetail, Match, NetworkGraph } from "../types/api";

interface Props {
  caseId?: number | string;
}

const props = defineProps<Props>();

// Read the route off the component proxy rather than useRoute(): that keeps
// the component mountable with a plain { $route } stub and still resolves
// through the real router in the app. A prop is accepted so tests can bypass
// the route entirely.
const proxy = getCurrentInstance()?.proxy as
  | { $route?: { params?: Record<string, string | string[]> } }
  | undefined;
const rawId = props.caseId ?? proxy?.$route?.params?.id;
const caseId = Number(Array.isArray(rawId) ? rawId[0] : rawId);

const detail = ref<CaseDetail | null>(null);
const matches = ref<Match[]>([]);
const loading = ref(false);
const error = ref("");
const sidebarOpen = ref(true);
const graphError = ref("");
const selectedEntityId = ref<number | null>(null);
const focusedNodeIds = ref<Set<string>>(new Set());
const actionError = ref("");

// Pass the ref itself so the composables react when matches.value is assigned.
const { filters, filtered: filteredMatches, resetFilters } = useMatchFilters(matches);
const summary = useRiskSummary(matches);

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
  for (const match of filteredMatches.value) {
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

function fitGraph() {
  cy?.fit(undefined, 24);
}

// Clicking a sidebar card focuses the entity in both the list and the graph,
// so the two panels stay in sync.
function focusEntity(entityId: number) {
  selectedEntityId.value = entityId;
  focusNode(`entity-${entityId}`, false);
  if (!cy) return;
  const node = cy.getElementById(`entity-${entityId}`);
  if (node.empty()) return;
  cy.elements().unselect();
  node.select();
  cy.animate(
    { center: { eles: node }, zoom: Math.max(cy.zoom(), 1) },
    { duration: 250 }
  );
}

// Focus mode: select one or more nodes and dim everything that is not directly
// connected to them. This lets an officer isolate a suspicious entity's local
// network without removing the rest of the graph.
function focusNode(nodeId: string, additive: boolean) {
  if (!cy) return;
  const node = cy.getElementById(nodeId);
  if (node.empty()) return;
  const next = new Set(focusedNodeIds.value);
  if (additive) {
    if (next.has(nodeId)) next.delete(nodeId);
    else next.add(nodeId);
  } else {
    next.clear();
    next.add(nodeId);
  }
  focusedNodeIds.value = next;
  updateGraphVisibility();
}

function clearFocus() {
  focusedNodeIds.value = new Set();
  selectedEntityId.value = null;
  updateGraphVisibility();
}

function groupResolved(group: EntityGroup) {
  return group.matches.length > 0 && group.matches.every((m) => m.resolved);
}

function groupResolution(group: EntityGroup) {
  return group.matches[0]?.resolution ?? "";
}

async function resolveGroup(group: EntityGroup, resolution: string) {
  actionError.value = "";
  const resolved = resolution !== "";
  try {
    const updated = await Promise.all(
      group.matches.map((m) => updateMatchResolution(m.id, resolved, resolution))
    );
    const byId = new Map<number, Match>(updated.map((m: Match) => [m.id, m]));
    matches.value = matches.value.map((m) => byId.get(m.id) ?? m);
  } catch (err) {
    actionError.value = err instanceof Error ? err.message : String(err);
  }
}

// Dim everything that fails the current filters instead of removing it, so
// the analyst keeps the surrounding context — the same pattern link-analysis
// tools (Linkurious, Maltego) use for linked list/graph views.
function updateGraphVisibility() {
  if (!cy) return;
  const visibleIds = new Set(filteredMatches.value.map((m) => `entity-${m.entity_id}`));
  const matchType = filters.value.matchType;

  // An entity counts as reviewed only when every one of its matches is.
  const matchesByEntity = new Map<number, Match[]>();
  for (const m of matches.value) {
    const list = matchesByEntity.get(m.entity_id) ?? [];
    list.push(m);
    matchesByEntity.set(m.entity_id, list);
  }
  const reviewByEntity = new Map<number, string>();
  for (const [entityId, entityMatches] of matchesByEntity) {
    if (entityMatches.every((m) => m.resolved)) {
      reviewByEntity.set(entityId, entityMatches[0].resolution);
    }
  }

  // When focus mode is active, the focused node(s) and their direct neighbours
  // stay visible even if filters would normally dim them.
  let focusVisibleIds: Set<string> | null = null;
  if (focusedNodeIds.value.size > 0) {
    const focused = cy!.collection();
    for (const id of focusedNodeIds.value) {
      focused.merge(cy!.getElementById(id));
    }
    focusVisibleIds = new Set(focused.closedNeighborhood().nodes().map((n) => n.id()));
  }

  cy.batch(() => {
    cy!.nodes().forEach((node) => {
      const isAgent = node.data("type") === "agent";
      const review = isAgent ? undefined : reviewByEntity.get(entityPk(node.id()));
      const filterDimmed = !isAgent && !visibleIds.has(node.id());
      const focusDimmed = focusVisibleIds !== null && !focusVisibleIds.has(node.id());
      node.toggleClass("dimmed", filterDimmed || focusDimmed);
      node.toggleClass("dismissed", review === "false_positive");
      node.toggleClass("confirmed", review === "confirmed");
    });
    cy!.edges().forEach((edge) => {
      const touchesHidden =
        edge.source().hasClass("dimmed") ||
        edge.target().hasClass("dimmed") ||
        edge.source().hasClass("dismissed") ||
        edge.target().hasClass("dismissed");
      const touchesAgent =
        edge.source().data("type") === "agent" || edge.target().data("type") === "agent";
      const wrongType = !!matchType && touchesAgent && edge.data("label") !== matchType;
      const focusDimmed =
        focusVisibleIds !== null &&
        (!focusVisibleIds.has(edge.source().id()) || !focusVisibleIds.has(edge.target().id()));
      edge.toggleClass("dimmed", touchesHidden || wrongType || focusDimmed);
    });
  });
}

function entityPk(nodeId: string) {
  return Number(nodeId.replace("entity-", ""));
}

// Cap node size with a log curve so highly-connected hubs don't become giant
// blobs that swallow their neighbours. A node with 1 link stays small; a node
// with 50 links only grows modestly, keeping the graph readable.
function nodeSize(degree: number) {
  const base = 22;
  const scale = 8;
  const max = 44;
  return Math.min(max, base + Math.log2(Math.max(1, degree)) * scale);
}

watch(filteredMatches, updateGraphVisibility);

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
        componentSpacing: 120,
        nodeOverlap: 20,
        idealEdgeLength: 100,
        nodeRepulsion: 1200000,
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
            label: (ele: cytoscape.NodeSingular) =>
              ele.degree() < 2 ? "" : ele.data("label"),
            "font-size": "10px",
            "background-color": "#607d8b",
            width: (ele: cytoscape.NodeSingular) => nodeSize(ele.degree()),
            height: (ele: cytoscape.NodeSingular) => nodeSize(ele.degree()),
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
          selector: "edge[category = 'shared'], edge[label *= 'shared']",
          style: { "line-color": "#f57c00", "target-arrow-color": "#f57c00" },
        },
        {
          selector: "edge[category = 'name'], edge[label *= 'name']",
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
        {
          selector: ".dimmed",
          style: {
            opacity: 0.12,
            "text-opacity": 0.15,
          },
        },
        {
          selector: "node.dismissed",
          style: {
            "background-color": "#9e9e9e",
            color: "#999",
            "text-opacity": 0.55,
          },
        },
        {
          selector: "node.confirmed",
          style: {
            "border-width": 4,
            "border-color": "#1b5e20",
            "border-opacity": 1,
          },
        },

      ],
    });

    // mapData("degree") has been replaced with function-based styles, so no
    // degree data field is needed; labels and sizes are computed live.

    cy.on("mouseover", "node", (evt) => {
      evt.target.style("label", evt.target.data("label"));
    });
    cy.on("mouseout", "node", (evt) => {
      // Restore the function-based label (hide low-degree labels again).
      evt.target.removeStyle("label");
    });

    // Click a node to focus it; Ctrl/Cmd+click to add/remove from the focus set.
    // Click the canvas background to clear focus.
    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      const originalEvent = evt.originalEvent as MouseEvent | undefined;
      const additive = !!(originalEvent?.ctrlKey || originalEvent?.metaKey);
      if (!additive) cy!.elements().unselect();
      node.select();
      focusNode(node.id(), additive);
      if (node.data("type") !== "agent") {
        selectedEntityId.value = entityPk(node.id());
      }
    });
    cy.on("tap", (evt) => {
      if (evt.target === cy) clearFocus();
    });

    cy.ready(fitGraph);
    updateGraphVisibility();
    // Dev-only hook so e2e tests can inspect graph state (canvas has no DOM).
    if (import.meta.env.DEV) {
      (window as unknown as { __cy?: Core }).__cy = cy;
    }
  } catch (err) {
    // jsdom and other headless containers have no layout box for cytoscape to
    // measure; the match list is still the useful half of the page, so keep
    // this failure local to the graph area instead of failing the whole view.
    graphError.value = err instanceof Error ? err.message : String(err);
  }
}

onMounted(async () => {
  if (!Number.isFinite(caseId) || caseId <= 0) return;
  loading.value = true;
  try {
    const [caseData, graph] = await Promise.all([getCase(caseId), getNetwork(caseId)]);
    detail.value = caseData;
    matches.value = caseData?.matches ?? [];
    // The graph container only exists once loading is false (it's inside the
    // v-else template), so flip the flag and wait a tick before rendering.
    loading.value = false;
    await nextTick();
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

    <template v-else>
      <p class="summary" v-if="detail">
        {{ detail.agent.name }} &middot; risk {{ detail.risk_score }} &middot;
        {{ detail.status }} &middot; {{ summary.uniqueEntityCount.value }} matched
        entit{{ summary.uniqueEntityCount.value === 1 ? "y" : "ies" }}
      </p>

      <div class="summary-bar" v-if="detail">
        <div class="summary-item">
          <strong>Highest confidence</strong>
          <span>{{ summary.highestConfidence.value }}</span>
        </div>
        <div class="summary-item">
          <strong>Strongest evidence</strong>
          <span>{{ summary.strongestTier.value || "—" }}</span>
        </div>
        <div class="summary-item" v-for="(count, type) in summary.matchTypeCounts.value" :key="type">
          <strong>{{ type }}</strong>
          <span>{{ count }}</span>
        </div>
      </div>

      <div class="panels" :class="{ 'sidebar-open': sidebarOpen }">
        <aside class="match-sidebar">
          <button
            type="button"
            class="toggle"
            @click="sidebarOpen = !sidebarOpen"
            :aria-expanded="sidebarOpen"
          >
            {{ sidebarOpen ? "Hide matches" : `Show matches (${summary.uniqueEntityCount.value})` }}
          </button>

          <div v-if="sidebarOpen" class="match-list-wrap">
            <div class="filters">
              <label>
                Match type
                <select v-model="filters.matchType">
                  <option value="">All</option>
                  <option value="identifier_exact">Identifier exact</option>
                  <option value="name_exact">Name exact</option>
                  <option value="name_fuzzy">Name fuzzy</option>
                  <option value="address_fuzzy">Address fuzzy</option>
                  <option value="network_2nd_degree">2nd-degree network</option>
                </select>
              </label>
              <label>
                Entity type
                <select v-model="filters.entityType">
                  <option value="">All</option>
                  <option value="person">Person</option>
                  <option value="organization">Organization</option>
                </select>
              </label>
              <label>
                Min confidence: {{ filters.minConfidence }}
                <input
                  type="range"
                  v-model.number="filters.minConfidence"
                  min="0"
                  max="100"
                  step="5"
                />
              </label>
              <button type="button" class="reset" @click="resetFilters">Reset filters</button>
            </div>

            <ul class="match-list">
              <li
                v-for="group in groupedMatches"
                :key="group.entity_id"
                class="entity-card"
                :class="{
                  selected: selectedEntityId === group.entity_id,
                  resolved: groupResolved(group),
                }"
                role="button"
                tabindex="0"
                @click="focusEntity(group.entity_id)"
                @keydown.enter="focusEntity(group.entity_id)"
              >
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
                <div class="card-actions" @click.stop @keydown.enter.stop>
                  <template v-if="groupResolved(group)">
                    <span class="resolution-badge" :class="groupResolution(group)">
                      {{ groupResolution(group) === "confirmed" ? "Confirmed hit" : "False positive" }}
                    </span>
                    <button type="button" class="reopen" @click="resolveGroup(group, '')">
                      Reopen
                    </button>
                  </template>
                  <template v-else>
                    <button type="button" class="confirm" @click="resolveGroup(group, 'confirmed')">
                      Confirm hit
                    </button>
                    <button type="button" class="dismiss" @click="resolveGroup(group, 'false_positive')">
                      False positive
                    </button>
                  </template>
                </div>
              </li>
              <li v-if="!groupedMatches.length" class="empty">No matches match the current filters.</li>
            </ul>
            <p v-if="actionError" class="error action-error">{{ actionError }}</p>
          </div>
        </aside>

        <div class="graph-wrap">
          <div class="graph-toolbar">
            <button type="button" @click="fitGraph">Fit graph</button>
            <button
              v-if="focusedNodeIds.size > 0"
              type="button"
              class="clear-focus"
              @click="clearFocus"
            >
              Clear focus
            </button>
          </div>
          <div class="graph-container" ref="graphEl">
            <p v-if="graphError" class="error graph-error">
              Graph could not be rendered: {{ graphError }}
            </p>
          </div>
          <div class="graph-legend" aria-label="Graph legend">
            <span class="legend-title">Nodes</span>
            <span class="legend-item"><i class="dot dot-agent"></i>Your agent</span>
            <span class="legend-item"><i class="dot dot-person"></i>Person</span>
            <span class="legend-item"><i class="dot dot-org"></i>Organization</span>
            <span class="legend-item"><i class="dot dot-confirmed"></i>Confirmed hit</span>
            <span class="legend-item"><i class="dot dot-dismissed"></i>Dismissed</span>
            <span class="legend-title">Agent matches</span>
            <span class="legend-item"><i class="line line-name"></i>Name match</span>
            <span class="legend-item"><i class="line line-direct"></i>Identifier / address match</span>
            <span class="legend-title">Entity links</span>
            <span class="legend-item"><i class="line line-shared"></i>Shared address / identifier</span>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.case-detail {
  container-type: inline-size;
}
.summary-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}
.summary-item {
  display: flex;
  flex-direction: column;
  min-width: 6rem;
}
.summary-item strong {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: #666;
}
.summary-item span {
  font-size: 0.95rem;
  font-weight: 600;
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
  max-height: 44rem;
  overflow-y: auto;
  border: 1px solid #ddd;
}
.filters {
  display: grid;
  gap: 0.5rem;
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}
.filters label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #444;
}
.filters select,
.filters input[type="range"] {
  width: 100%;
}
.reset {
  justify-self: start;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  cursor: pointer;
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
  cursor: pointer;
}
.entity-card:hover {
  border-color: #bbb;
}
.entity-card.selected {
  border-color: #1976d2;
  box-shadow: 0 0 0 1px #1976d2;
}
.entity-card.resolved {
  opacity: 0.5;
  background: #ececec;
}
.card-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.5rem;
}
.card-actions button {
  font-size: 0.72rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
}
.card-actions .confirm:hover {
  border-color: #1b5e20;
  color: #1b5e20;
}
.card-actions .dismiss:hover {
  border-color: #b71c1c;
  color: #b71c1c;
}
.resolution-badge {
  font-size: 0.72rem;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  font-weight: 600;
}
.resolution-badge.confirmed {
  background: #e8f5e9;
  color: #1b5e20;
}
.resolution-badge.false_positive {
  background: #fbe9e7;
  color: #b71c1c;
}
.action-error {
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
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
  position: relative;
}
.graph-legend {
  position: absolute;
  left: 0.5rem;
  bottom: 0.5rem;
  z-index: 10;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.75rem;
  max-width: 70%;
  padding: 0.4rem 0.6rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.7rem;
  color: #444;
}
.legend-title {
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.62rem;
  color: #888;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  white-space: nowrap;
}
.dot {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
  display: inline-block;
}
.dot-agent {
  background: #1976d2;
}
.dot-person {
  background: #d84315;
}
.dot-org {
  background: #2e7d32;
}
.dot-confirmed {
  background: #fff;
  border: 2px solid #1b5e20;
  box-sizing: border-box;
}
.dot-dismissed {
  background: #9e9e9e;
  opacity: 0.6;
}
.line {
  width: 1.2rem;
  height: 0;
  border-top: 2px solid #bbb;
  display: inline-block;
}
.line-name {
  border-top-color: #1976d2;
}
.line-shared {
  border-top-color: #f57c00;
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
.graph-error {
  padding: 1rem;
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
