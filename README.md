<!-- # SanctionsGraph -->

<img src="./assets/logo.svg" alt="SanctionsGraph logo" width="120" />

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js)
![Postgres](https://img.shields.io/badge/PostgreSQL-pg__trgm-4169E1?logo=postgresql)


SanctionsGraph is a FinTech compliance intelligence tool that combats against sanctions violations. 


What it does
----
It screens education agents and international applicants against global sanctions lists, then visualzies hidden risk connections (shared addresses, phone numbers, banking details) as an interactive graph. 

Project goals:
----
1. learn more about challenges and solutions in fintech/ed-tech. 
2. learn how to wire restful apis & database in django, how to make components in vue.js and work with postgresql database and integrate them with one another. 
3. quench my curiosity ... 

<!-- 
```
- "Flywire's own 10-K admits they are under active OFAC investigation for sanctions violations." (Page 28, Item 1A)
- "A Florida school was fined $1.72 million by OFAC for failing to screen tuition payors."
- "The industry false-positive rate is 90–95%, meaning compliance teams drown in noise — my graph approach makes the 'why' visible and auditable."
``` -->


## Domain terminologies

In order to better understand the problem that we are solving, one must acquaint himself with the following vocabulary.

**Sanctions list:** A government register of people and organisations you are legally
barred from doing business with. Payments to anyone on one must be blocked, not just
flagged.

**OFAC:** The US Office of Foreign Assets Control, which publishes and enforces the best
known lists. Penalties reach roughly $377,700 per violation, or twice the transaction
value.

**SDN List:** Specially Designated Nationals, OFAC's main list of blocked persons and
entities.

**PEP:** Politically Exposed Person. Someone holding a prominent public role, or their
close family and associates. Not illegal to deal with, but higher risk of corruption or
bribery, so it warrants extra scrutiny rather than an outright block.

**Education agent:** A recruiter paid commission to place international students with
universities. They handle tuition money, which is what brings them inside the scope of
sanctions and AML rules. They are the subject being screened here.

**KYC / AML:** Know Your Customer and Anti-Money Laundering. The regulatory obligation to
identify who you are dealing with and where their money came from.

**UBO:** Ultimate Beneficial Owner. The real human behind a chain of companies. Layers of
shells exist precisely to obscure this, which is why ownership is worth modelling as a
graph.

**False positive:** An alert that turns out to be the wrong person. Around 90 to 95% of
alerts are false positives, so an analyst's real job is dismissing noise, not finding
hits. That is the constraint this project is built around: every match carries a
human-readable explanation so it can be dismissed quickly and defensibly.

### The data

**OpenSanctions:** An open dataset consolidating sanctions lists and PEP registers from
many jurisdictions into one schema. This project ingests its bulk download.

**FollowTheMoney (FtM):** The schema OpenSanctions publishes in. Every record has the
same envelope (`id`, `caption`, `schema`, `properties`, `datasets`, `target`) but the
keys inside `properties` vary by schema, and every value is a list even when there is
only one item.

**Target:** An FtM record with `target: true` is sanctioned or wanted in its own right.
`target: false` means it is a related party, pulled in because it is connected to
someone who is. Stored as `SanctionedEntity.is_target` and used to weight the risk score.

### This project's own vocabulary

**Screening case:** One run of the matcher against one agent. Holds the risk score, the
review status (`open` or `resolved`), and a `network_snapshot`: the graph frozen as it
was at run time, so an old decision stays auditable after the sanctions data refreshes.

**Match:** One hit inside a case. Carries a match type, a confidence from 0 to 100, an
explanation, and the reviewer's verdict.

**Evidence tiers:** The five match types, ranked strongest to weakest. New matching logic
maps onto these rather than inventing a parallel score:

| Tier | Meaning | Confidence |
| --- | --- | --- |
| `identifier_exact` | Same passport, tax ID, or company registration number | 100 |
| `name_exact` | Name or alias matches exactly | 95 |
| `name_fuzzy` | Name is a close but inexact match | similarity score |
| `address_fuzzy` | Address is a close match | similarity score, penalised if broad |
| `network_2nd_degree` | Not directly matched, but two hops away through a shared attribute | 50 |

**Trigram similarity:** How the fuzzy tiers work. Postgres' `pg_trgm` extension splits
strings into three-character chunks and scores the overlap. `similarity('Sergey Lavrov',
'Sergei Lavrov')` is 0.75, which clears the 0.6 threshold.

**Broad address:** A free-text address so generic that matching on it is meaningless.
"Hong Kong" hits 128 entities. Confidence on such matches is scaled down, and the
screening form warns before submission.

**2nd-degree link:** An entity reached not by matching the agent directly, but by
following a shared address or identifier from something that did match. This is where a
graph earns its place: it surfaces relationships a flat list of alerts hides.



## Work in progress, TODO: 
- Refactor the current codebase by creating a python package for each service. 
- Create CI/CD pipelines for both the backend and frontend via GitHub Action. 
- Fix all pylance and pyright issue using mypy static typechecker ... 
- Fix all unreachable path errors. 
- Synchronize the postgresql db running locally in my docker desktop with the one running in neon to avoid unexpected behavior ... 




## Core engineering concepts
- Preserving traceability from the original record once an association is detected between an education agent and an entity from the sanction list.
- Building reusable `views` and `components` in Vue.js 
- Architecting Restful APIs
- Building multi-tenant software 
- Using agentic workflows to efficiently argument speed of design (brainstorming), implementation and testing.  





## Try it

**[sanctions.seth-tang.me](https://sanctions.seth-tang.me/)**

Frontend and backend both run on Vercel, with Postgres on Neon. The backend is a
serverless function, so there could be a bit of a delay depending on who accesses the webpage first.

The live database holds a snapshot of roughly 50,000 sanctioned entities. It is
refreshed by hand rather than on a schedule, so it will drift behind
OpenSanctions over time.




## Tech stack

| Layer | Built with | Hosted on |
| --- | --- | --- |
| Frontend | Vue 3 (Composition API), TypeScript, Vite, Cytoscape | Vercel |
| Backend | Django 6.1 + Django REST Framework | Vercel (serverless function) |
| Database | PostgreSQL with the `pg_trgm` extension for fuzzy matching | Neon |
| Testing | pytest and pytest-django; Vitest and Playwright | run locally |

Fuzzy name and address matching is done in Postgres with trigram `similarity()`
rather than in Python, and second-degree network links are found with NetworkX.

<!-- Both ci and cd workflows were created for both frontend and backend using GitHub Action. -->


## Building & running

Postgres is required. The project does not fall back to SQLite.

**Prerequisites:** Docker, [uv](https://docs.astral.sh/uv/), Node 20+

### 1. Database

```bash
docker run -d --name sg-postgres \
  -e POSTGRES_USER=sguser -e POSTGRES_PASSWORD=sgpass \
  -e POSTGRES_DB=sanctionsgraph -p 5432:5432 postgres:15
```

If a native `postgresql` service is already bound to 5432 it will answer instead of the
container, and `migrate` fails with `password authentication failed for user "sguser"`.
Check with `sudo lsof -i :5432` and stop the native service.

### 2. Backend: http://localhost:8000

```bash
cd backend
uv sync
uv run manage.py migrate
uv run manage.py createsuperuser   # optional, for /admin/
uv run manage.py runserver
```

### 3. Frontend: http://localhost:5173

```bash
cd frontend
npm install
npm run dev
```

### 4. Loading sanctions data

<!-- As the PostgreSQL database is being provisioned via Neon, one does not need to  -->

<!-- I almost forgot that the backend is not configured to speak w -->

At the moment, as the software was built to be more of a demo, the backend is connected to PostgreSQL which
is being provisioned via Neon. However, it's difficult to not expect misuse or abuse of the `/`


The screening pipeline works against an empty database, but there is nothing to match.
The source dump is roughly 2.6 GB and is streamed line by line rather than loaded into
memory. **Start with `--limit`** so a first run takes minutes rather than an hour.

```bash
curl -o backend/data/entities.ftm.json \
  https://data.opensanctions.org/datasets/latest/default/entities.ftm.json

cd backend
uv run manage.py ingest_opensanctions --limit 5000
```

Re-running is safe: entities are upserted on the OpenSanctions `source_id`.

### Tests

```bash
cd backend  && uv run pytest        # Django: models, matcher, API
cd frontend && npx vitest run       # Vue components + composables
cd frontend && npm run test:e2e     # Playwright, boots the dev server itself
cd frontend && npm run build        # vue-tsc, type errors fail the build
```

Day-by-day terminal transcripts of the above live in [`.logbook/`](.logbook/).


## Support

Let me know if you have issues tangpiseth43@gmail.com

License
-------

The code in this repository is MIT licensed. See [LICENSE](LICENSE).

The OpenSanctions dataset it consumes is **not** covered by that license. It is
published under CC BY-NC 4.0, and OpenSanctions treats compliance screening as
commercial use regardless of whether it generates revenue. Non-commercial use
(student projects, personal research) needs no permission; use inside a
for-profit business requires a data license from them.




# References

## Data sources

- [OpenSanctions docs](https://www.opensanctions.org/docs/): entity matching, bulk
  downloads, and the FollowTheMoney data model this project ingests.
- [OpenSanctions API](https://www.opensanctions.org/docs/api/): the hosted `/match`
  endpoint, an alternative to ingesting the bulk file.
- [OpenSanctions Swagger UI](https://api.opensanctions.org/docs): interactive API docs.
- [OFAC official website](https://ofac.treasury.gov/): the US sanctions authority.
- [SDN List](https://en.wikipedia.org/wiki/Specially_Designated_Nationals_and_Blocked_Persons_List)
  Specially Designated Nationals, the best known sanctions list.
- [US government sanctions](https://en.wikipedia.org/wiki/United_States_government_sanctions)
  and [OFAC](https://en.wikipedia.org/wiki/Office_of_Foreign_Assets_Control) primers.

## Why this project exists

The premise is that screening alerts are overwhelmingly noise, so the useful output is an
auditable explanation rather than a score.

- ["The Problem of False Positives in AML Screening"](https://www.sanctions.io/blog/the-problem-of-false-positives-in-aml-screening)
  **90 to 95% of alerts are false positives.** This is the number the whole design
  responds to.
- ["How to Reduce False Positives in Sanctions Screening"](https://www.sardine.ai/blog/rules-to-reduce-false-positives-in-sanctions-screening)
  institutions spend 5 to 10 minutes per alert and resolve under 10% as true matches.
- ["Sanctions Screening Challenges and Best Practices"](https://www.feedzai.com/blog/sanctions-screening/)
  why regulators now expect holistic matching, not just name comparison.
- ["Why False Positives No Longer Matter in AML"](https://www.workfusion.com/blog/false-positives-do-not-matter-in-aml/)
  the counter-argument: automate the volume instead of tuning thresholds.
- ["OFAC Meaning: What Is the Office of Foreign Assets Control?"](https://www.innreg.com/blog/ofac-meaning)
  penalties reach $377,700 per violation, or twice the transaction value.
- [OFAC video series](https://ofac.treasury.gov/ofac-video-series) and a
  [13-part playlist](https://www.youtube.com/playlist?list=PL0Pufzwcosu-9zpy41pyugHN08aR5OXm-)
  covering the 50% rule, false positives, and evasion red flags.

## Further reading

<details>
<summary>Books on sanctions and financial crime (6)</summary>

| Book | Author | Why read it |
| --- | --- | --- |
| *Sanctions Screening: A Key Element of AML and Financial Crime Prevention* | CA Mayur Joshi & Vedant Sangit | The most directly applicable of these. 144 pages on how screening systems work, evasion techniques, and building a compliance program. |
| *The Art of Sanctions: A View from the Field* | Richard Nephew | Written by an architect of the Iran sanctions. Covers why sanctions exist and what they are meant to achieve. |
| *Backfire* | Agathe Demarais | How evasion works in practice, and how overuse of sanctions creates workaround economies. |
| *Moneyland* | Oliver Bullough | Offshore finance and how wealth is hidden. Useful intuition for why ultimate beneficial ownership matters in a graph model. |
| *Billion Dollar Whale* | Tom Wright & Bradley Hope | The 1MDB scandal. Shows how intermediaries exploit siloed bank KYC, which is the network problem this tool targets. |
| *Mastering Anti-Money Laundering and Counter-Terrorist Financing* | Tim Parkman | Operational guide to AML programs, transaction monitoring, and SARs. |

</details>

## Prior art and tools

- [Kharon API](https://www.kharon.com/products/api): a commercial equivalent.
- [PuppyGraph: compliance graph](https://www.puppygraph.com/blog/compliance-graph)
  graph modelling for compliance data.
- [Microsoft OpenSanctions connector](https://learn.microsoft.com/en-us/connectors/opensanctions/)
  how enterprises wire OpenSanctions into Power Automate.
- [D3.js](https://d3js.org): considered for the graph view; this project uses Cytoscape.
- [GitHub CLI](https://github.com/cli/cli#installation): used for the branch and PR flow.
- [Method Draw](https://editor.method.ac/): used to hand-edit `logo.svg`.
- [rsms/rsm `.logbook`](https://github.com/rsms/rsm/tree/main/.logbook): the inspiration
  for keeping a dated dev journal in the repo.
- [mypy static python typechecker](https://mypy.readthedocs.io/en/stable/existing_code.html)
