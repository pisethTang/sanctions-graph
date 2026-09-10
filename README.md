<!-- # SanctionsGraph -->

<img src="./assets/logo.svg" alt="SanctionsGraph logo" width="120" />

SanctionsGraph is a FinTech compliance intelligence tool that combats against sanctions violations. 


What it does
----
It screens education agents and international applicants against global sanctions lists, then visualzies hidden risk connections (shared addresses, phone numbers, banking details) as an interactive graph. 

Project goals:
----
1. learn more about challenges and solutions in fintech/ed-tech. 
2. have fun -- simplicity 
3. quench my curiosity ... 

<!-- 
```
- "Flywire's own 10-K admits they are under active OFAC investigation for sanctions violations." (Page 28, Item 1A)
- "A Florida school was fined $1.72 million by OFAC for failing to screen tuition payors."
- "The industry false-positive rate is 90–95%, meaning compliance teams drown in noise — my graph approach makes the 'why' visible and auditable."
``` -->


## Key terminologies (WIP)
1. PEP: 
2. OpenSanctions Data


<!-- 
## Work in progress, TODO: 
-  -->

## Core engineering concepts
- Preserving traceability from the original record once an association is detected between an education agent and an entity from the sanction list.
- 


## Try it

**[sanctions.seth-tang.me](https://sanctions.seth-tang.me/)**

Frontend and backend both run on Vercel, with Postgres on Neon. The backend is a
serverless function, so the first request after a quiet spell takes an extra
half second to wake up.

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

### 4. Loading sanctions data (optional)

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
