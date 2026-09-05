Finally initialized the backend and frontend. And now I will need to think about the requirements carefully by answering the following questions.

# Architecture

## 1. The Data Model (PostgreSQL)

- [ ] **Question 1.1** — What does an "Agent" look like?

  An education agent is not just a name.

  What fields do we collect?
  - Full legal name
  - Trading name / DBA
  - Date of birth (for individual agents) or incorporation date (for agencies)
  - Nationality / country of registration
  - Passport number, business registration number, tax ID
  - Physical office address(es)
  - Email domain, phone number
  - Associated sub-agents or partner agencies

  Why this matters: OpenSanctions entities have deeply nested properties. If your Agent model is flat (just name, country), you cannot do meaningful 2nd-degree matching. If it is too deep, you over-engineer. Decide the canonical Agent schema now.

- [ ] **Question 1.2** — What is a "SanctionedEntity" in our system?

  OpenSanctions returns entities of type Person, Organization, LegalEntity, Vessel, Aircraft. Do we store all types or filter to Person and Organization only?

- [ ] **Question 1.3** — How do we normalize aliases?

  OpenSanctions gives aliases as a list: `["Vladimir Putin", "Владимир Путин", "Vladimir Vladimirovich Putin"]`. Do we:
  - Store each alias as a separate row in an aliases table?
  - Store one "canonical name" and dump the rest as JSONB?
  - Normalize transliterations (e.g., Cyrillic → Latin) at ingest time or at query time?

- [ ] **Question 1.4** — What is an "Address" in our domain?

  Is it free-text ("123 Main St, Boston, MA") or structured (street, city, country_code)? OpenSanctions addresses are messy. If you store free-text, pg_trgm works well. If you structure them, you need a parser.

- [ ] **Question 1.5** — What is an "Identifier"?

  Passport numbers, tax IDs, business registration numbers, IMO numbers (for ships). Do we store the type (passport, tax_id) and the value? Do we hash sensitive identifiers?

- [ ] **Question 1.6** — What is the "screening result" we persist?

  When I screen an agent, what gets saved?
  - The raw match list?
  - The computed graph (nodes/edges) as JSONB?
  - Just the summary (highest risk score, number of hits)?
  - A snapshot of the OpenSanctions data at the time of screening (for audit)?

  Why this matters: If a regulator asks "why was this agent flagged on August 15th?" and OpenSanctions has since updated their data, you need an immutable audit trail.

## 2. The Matching Engine (The "90% Recall" Bullet)

- [ ] **Question 2.1** — What is the matching pipeline?

  Propose the flow:
  1. Exact match on identifiers (passport, tax ID) → if hit, 100% confidence, stop?
  2. Exact match on name (any alias) → high confidence
  3. Fuzzy match on name (pg_trgm similarity > 0.6?) → medium confidence
  4. Fuzzy match on address → low confidence
  5. NetworkX graph traversal from matched entities to find 2nd-degree connections via shared addresses/identifiers → risk increment

  Is this the right order? Do we short-circuit or run everything and aggregate?

- [ ] **Question 2.2** — What is the "graph" we build in NetworkX?

  - Nodes = SanctionedEntity + Agent? Or just SanctionedEntity and we inject the Agent at query time?
  - Edges = shares_address, shares_identifier, family_member, business_associate?
  - Edge weights = all 1.0, or weighted by confidence?

- [ ] **Question 2.3** — What does "2nd-degree" mean precisely?

  - Agent → shares address with Entity A → Entity A is family member of Sanctioned Entity B = 2nd degree?
  - Agent → shares identifier with Entity A → Entity A is business associate of Entity B = 2nd degree?

  Do we cap at 2nd degree or go to 3rd?

- [ ] **Question 2.4** — How do we score risk?

  - Is it binary (flagged / not flagged) or a score (0–100)?
  - Does a direct name match score higher than a 2nd-degree network connection?
  - Does a PEP hit score differently than a sanctions hit?

- [ ] **Question 2.5** — What is the performance budget?

  Screening 50,000 OpenSanctions records with NetworkX graph traversal in a single Django request: how long is acceptable? 500ms? 2s? 10s?

  If it is too slow, do we pre-compute the graph at ingest time (materialized view) or compute on demand?

## 3. The API Contract (Django REST Framework)

- [ ] **Question 3.1** — Who calls this API?

  - A Vue.js frontend (human compliance officer)?
  - Another service (batch upload of 1,000 agents)?
  - Both?

- [ ] **Question 3.2** — What are the core resources?

  Propose them:
  - Agent (CRUD)
  - ScreeningCase (create = run screening, read = view results)
  - Match (read-only, child of ScreeningCase)
  - Network (read-only, derived from a ScreeningCase)

- [ ] **Question 3.3** — What does the Cytoscape endpoint return?

  - Option A: `GET /api/cases/123/network/` returns `{ nodes: [...], edges: [...] }` in Cytoscape JSON format.
  - Option B: The frontend builds the graph from matches data.
  - Option C: Both — the backend returns raw matches, and a separate endpoint returns pre-formatted Cytoscape elements.

- [ ] **Question 3.4** — Do we need pagination?

  If an agent matches 200 sanctioned entities (rare but possible with common names), does the API paginate matches? Does the graph endpoint paginate nodes?

- [ ] **Question 3.5** — Authentication & Authorization

  - Do we need auth for a portfolio project?
  - If yes, simple JWT or Django session auth?
  - Who can create a screening? Who can view results?

## 4. The Frontend (Vue.js 3 + Cytoscape.js)

- [ ] **Question 4.1** — What are the user-facing screens?

  List them:
  - Agent onboarding form (create agent, trigger screening)
  - Case list (all screenings, sortable by date/risk)
  - Case detail (split view: match list left, graph right)
  - ???

- [ ] **Question 4.2** — What happens when a compliance officer clicks a graph node?

  - Show entity details in a sidebar?
  - Navigate to the OpenSanctions source page?
  - Expand the node's own 1st-degree connections (lazy load)?

- [ ] **Question 4.3** — What is the "false positive resolution" workflow?

  The resume says "resolve false positives." What does that mean in the UI?
  - A button "Mark as False Positive" on a match?
  - A notes field for the officer to explain why it is a false positive?
  - Does the system learn from this (no, not in MVP) or just record it?

## 5. Testing & Quality (The "100% pytest" Bullet)

- [ ] **Question 5.1** — What is the test pyramid?

  - Unit tests: matcher service, model methods, utility functions
  - Integration tests: API endpoints with test database
  - E2E tests: Vue frontend with mocked API?

- [ ] **Question 5.2** — What are the critical edge cases?

  List the ones that must pass:
  - Agent with no matches → empty result, no crash
  - Agent with exact name match → 100% confidence
  - Agent with fuzzy name match (typo) → flagged
  - Agent sharing address with a sanctioned entity's associate → 2nd-degree flag
  - Duplicate screening of same agent → idempotent or new case?

- [ ] **Question 5.3** — How do we test NetworkX graph logic?

  Do we mock the graph data or build a small known graph in `setUp()`?

## 6. Deployment & Infrastructure

- [ ] **Question 6.1** — What is the local dev stack?

  - Docker Compose with PostgreSQL + Django + Vue?
  - Or native Python/Node with local PostgreSQL?

- [ ] **Question 6.2** — What is the production data strategy?

  - OpenSanctions bulk JSON: download once, ingest on deploy, or cron job to refresh weekly?
  - Do we store the full OpenSanctions dataset (GBs) or a filtered subset (PEP + sanctions only)?

- [ ] **Question 6.3** — Environment variables

  What secrets do we need?
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `OPENSACTIONS_API_KEY` (if using API instead of bulk)
  - `NEWSAPI_KEY`
  - `CORS_ALLOWED_ORIGINS`

## 7. The AI-Augmented Workflow (The "Claude Code" Bullet)

- [ ] **Question 7.1** — What do we prompt Claude Code for?

  - Django models and migrations?
  - The OpenSanctions JSON normalizer?
  - The NetworkX matcher service?
  - Vue components?
  - All of the above?

- [ ] **Question 7.2** — What do we manually audit?

  The resume says "manually audited for SQL injection safety." What does that mean in practice?
  - Check every `.raw()` or `.extra()` query?
  - Verify all user input is parameterized?
  - Review every `eval()` or `exec()` (there should be none)?
