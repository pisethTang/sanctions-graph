import { test, expect, type Page } from "@playwright/test";

const casePayload = {
  id: 1,
  agent: {
    id: 1,
    name: "Test Agent",
    nationality: "ru",
    aliases: [],
    addresses: [],
    created_at: "2026-09-08T10:00:00Z",
  },
  risk_score: 100,
  status: "open",
  matches: [
    {
      id: 1,
      entity_id: 101,
      entity_name: "Sergei Lavrov",
      entity_type: "person",
      source_id: "NK-demo-pep",
      match_type: "name_exact",
      confidence: 95,
      explanation: "Name matches sanctioned record 'Sergei Lavrov'",
      resolved: false,
      resolution: "",
      created_at: "2026-09-08T10:00:00Z",
    },
  ],
  network_snapshot: null,
  created_at: "2026-09-08T10:00:00Z",
};

const networkPayload = {
  nodes: [
    { data: { id: "agent-1", label: "Test Agent", type: "agent", risk_score: 100 } },
    { data: { id: "entity-101", label: "Sergei Lavrov", type: "person" } },
  ],
  edges: [{ data: { source: "agent-1", target: "entity-101", label: "name_exact" } }],
};

const CASE_ROUTE = "**/api/cases/1/";
const NETWORK_ROUTE = "**/api/cases/1/network/";

function mockCaseApi(page: Page) {
  return page.route(CASE_ROUTE, async (route) => {
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(casePayload) });
  });
}

function mockNetworkApi(page: Page) {
  return page.route(NETWORK_ROUTE, async (route) => {
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(networkPayload) });
  });
}

test.beforeEach(async ({ page }) => {
  await mockCaseApi(page);
  await mockNetworkApi(page);
});

test("renders the matched entity card after the API resolves", async ({ page }) => {
  await page.goto("/cases/1");

  await expect(page.getByRole("heading", { name: "Case 1" })).toBeVisible();
  await expect(page.locator(".entity-card")).toBeVisible();
  await expect(page.locator(".entity-card")).toContainText("Sergei Lavrov");
});

test("renders the network graph after the API resolves", async ({ page }) => {
  await page.goto("/cases/1");

  // Cytoscape injects canvas elements into the container once it initializes.
  const canvas = page.locator(".graph-container canvas").first();
  await expect(canvas).toBeVisible();
  const box = await canvas.boundingBox();
  expect(box?.width).toBeGreaterThan(0);
  expect(box?.height).toBeGreaterThan(0);
  await expect(page.locator(".graph-error")).toHaveCount(0);
  await expect(page.locator(".graph-legend")).toBeVisible();
  await expect(page.locator(".graph-legend")).toContainText("Your agent");
  await expect(page.locator(".graph-legend")).toContainText("Shared address / identifier");
});

test("filtering the sidebar dims non-matching graph elements", async ({ page }) => {
  await page.goto("/cases/1");

  await expect(page.locator(".entity-card")).toBeVisible();

  // No identifier_exact matches exist in the mock data, so selecting it
  // should empty the sidebar and dim every entity node in the graph.
  await page.getByLabel("Match type").selectOption("identifier_exact");
  await expect(page.locator(".match-list")).toContainText("No matches match the current filters.");

  const counts = await page.evaluate(() => {
    const cy = (window as unknown as { __cy: any }).__cy;
    return {
      totalNodes: cy.nodes().length,
      dimmedNodes: cy.nodes(".dimmed").length,
      dimmedEdges: cy.edges(".dimmed").length,
    };
  });

  // The agent node stays visible; both entity nodes and the edge are dimmed.
  expect(counts.dimmedNodes).toBe(counts.totalNodes - 1);
  expect(counts.dimmedEdges).toBeGreaterThan(0);

  // Resetting restores full visibility.
  await page.getByRole("button", { name: "Reset filters" }).click();
  const afterReset = await page.evaluate(() => {
    const cy = (window as unknown as { __cy: any }).__cy;
    return cy.elements(".dimmed").length;
  });
  expect(afterReset).toBe(0);
});

test("clicking a sidebar card selects and centers its node", async ({ page }) => {
  await page.goto("/cases/1");

  const card = page.locator(".entity-card");
  await expect(card).toBeVisible();
  await card.click();

  await expect(card).toHaveClass(/selected/);
  const selectedId = await page.evaluate(() => {
    const cy = (window as unknown as { __cy: any }).__cy;
    return cy.$("node:selected").id();
  });
  expect(selectedId).toBe("entity-101");
});

test("an officer can dismiss a match as a false positive from the card", async ({ page }) => {
  await page.route("**/api/matches/1/", async (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ...casePayload.matches[0],
        resolved: true,
        resolution: "false_positive",
      }),
    });
  });

  await page.goto("/cases/1");
  await expect(page.locator(".entity-card")).toBeVisible();

  await page.locator(".card-actions .dismiss").click();

  await expect(page.locator(".resolution-badge")).toHaveText("False positive");
  await expect(page.locator(".entity-card")).toHaveClass(/resolved/);

  // The graph node reflects the review decision too.
  const nodeClasses = await page.evaluate(() => {
    const cy = (window as unknown as { __cy: any }).__cy;
    const node = cy.getElementById("entity-101");
    return { dismissed: node.hasClass("dismissed"), confirmed: node.hasClass("confirmed") };
  });
  expect(nodeClasses.dismissed).toBe(true);
  expect(nodeClasses.confirmed).toBe(false);
});

test("shows the correct match count and summary stats", async ({ page }) => {
  await page.goto("/cases/1");

  await expect(page.locator(".summary")).toContainText("1 matched entity");
  await expect(page.locator(".summary")).toContainText("risk 100");
  await expect(page.locator(".summary-bar")).toContainText("name_exact");
});

test("renders an empty state when the case has no matches", async ({ page }) => {
  await page.unroute(CASE_ROUTE);
  await page.route(CASE_ROUTE, async (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ...casePayload, matches: [], risk_score: 0 }),
    });
  });

  await page.goto("/cases/1");

  await expect(page.locator(".summary")).toContainText("0 matched entities");
  await expect(page.locator(".match-list")).toContainText("No matches match the current filters.");
});
