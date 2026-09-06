# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SanctionsGraph screens education agents / international applicants against global sanctions
and PEP lists (OpenSanctions data), then visualizes the *why* behind a hit — shared addresses,
identifiers, and 2nd-degree network links — as an interactive graph. The domain premise
(documented in `README.md`) is that 90–95% of screening alerts are false positives, so the
product value is auditable explanations, not just a match score.

It is an early-stage learning project: the data model is in place, the API layer is not yet built.

## Repo layout

- `backend/` — Django 6.1 + DRF project `sanctionsgraph`, single app `screening`. Managed with `uv`.
- `frontend/` — Vue 3 (`<script setup>`, Composition API) + TypeScript + Vite.
- `.logbook/` — dated dev journal (`DD-Month-YYYY.md`). Each day's file records what was
  attempted, what broke, and the fix. Design decisions (e.g. the OpenSanctions field mapping)
  are worked out here before they land in code, so read the latest entries for current intent.

## Commands

Backend (run from `backend/`, all Django commands go through `uv run`):

```bash
uv sync                                   # install deps from uv.lock
uv run manage.py runserver                # dev server on :8000
uv run manage.py makemigrations screening
uv run manage.py migrate
uv run manage.py dbshell
uv run pytest                             # see caveat below
uv run pytest screening/tests.py::TestName::test_case   # single test
```

Frontend (run from `frontend/`):

```bash
npm install
npm run dev        # Vite dev server
npm run build      # vue-tsc -b && vite build — type errors fail the build
npm run preview
```

Postgres (required — the project does not fall back to SQLite):

```bash
docker run -d --name sg-postgres \
  -e POSTGRES_USER=sguser -e POSTGRES_PASSWORD=sgpass -e POSTGRES_DB=sanctionsgraph \
  -p 5432:5432 postgres:15
```

If `migrate` reports `password authentication failed for user "sguser"`, the usual cause is a
native `postgresql` service already bound to 5432 answering instead of the container
(`sudo lsof -i :5432`). Stop the native service, then recreate the container.

## Data model (`backend/screening/models.py`)

The seven models encode the screening pipeline, and each one exists to preserve traceability
back to the source record:

- `Agent` — the subject being screened.
- `SanctionedEntity` — a person or organization from OpenSanctions; `source_id` is the
  OpenSanctions ID and is `unique`, so ingestion must upsert on it.
- `EntityAlias` / `EntityAddress` / `EntityIdentifier` — the match surfaces. Aliases and
  `EntityAddress.full_text` are intended for fuzzy matching (`pg_trgm`); identifiers are
  exact-match only and are stored as SHA-256 of the stripped, upper-cased value via
  `EntityIdentifier.hash_value()` — never store a raw passport or tax number.
- `ScreeningCase` — one screening run; `network_snapshot` (JSON) freezes the graph as it was
  at run time so an old decision stays auditable after the data refreshes.
- `Match` — one hit, carrying `match_type`, `confidence`, and a human-readable `explanation`,
  plus `resolved`/`resolution` for the officer's false-positive verdict. `match_type` choices
  (`identifier_exact` → `network_2nd_degree`) are the ranked evidence tiers; keep new matching
  logic mapped onto them rather than inventing parallel scoring.

## OpenSanctions ingestion

Source data is the FollowTheMoney JSON-lines dump
(`https://data.opensanctions.org/datasets/latest/default/entities.ftm.json`), downloaded to
`backend/data/entities.ftm.json` (~2.6 GB, untracked and **not** in `.gitignore` — do not
`git add` it, and stream it line by line rather than loading it).

Every record has the same envelope (`id`, `caption`, `schema`, `properties`, `datasets`,
`target`) but the keys inside `properties` differ by schema, and every value is a list even
when there is one item. Mapping used by this project (worked out in `.logbook/06-September-2026.md`):

| FtM field | Destination |
| --- | --- |
| `id` | `SanctionedEntity.source_id` |
| `schema` (`Person` / `Company` / …) | `SanctionedEntity.entity_type` |
| `properties.name[0]` | `SanctionedEntity.name` |
| `properties.alias[]` | `EntityAlias` |
| `properties.address[]` | `EntityAddress` |
| `passportNumber`, `taxNumber`, `idNumber`, `registrationNumber`, `innCode`, `ogrnCode`, `leiCode` | `EntityIdentifier` (hashed) |

`alias` and `address` are frequently absent on `Person` records; handle missing keys rather
than assuming the Company shape. `target: true` means the entity itself is sanctioned/wanted.

## Current state — read before assuming something exists

- `screening/views.py`, `screening/tests.py`, and `sanctionsgraph/urls.py` are still Django
  stubs. There are no serializers, no API routes beyond `/admin/`, and no ingestion command yet.
- `frontend/src/main.ts` mounts `App.vue` directly and does **not** install the router; the
  router and `Home.view.vue` are scaffolded but unreachable. Wire `app.use(router)` and a
  `<RouterView/>` when the first real route is needed.
- The frontend talks to the backend via `backend_origin` in `src/constants/constants.ts`
  (`http://localhost:8000`); backend errors are typed as `BackendError = Record<string, string[]>`
  (DRF's field-errors shape).
- `pytest-django` is installed but unconfigured — there is no `DJANGO_SETTINGS_MODULE` setting
  in `pyproject.toml`/`pytest.ini` and no `conftest.py`, so bare `pytest` will not bootstrap
  Django until that is added.
- `settings.py` still holds the generated `SECRET_KEY`, `DEBUG = True`, and hard-coded DB
  credentials, while `backend/screening/.env` (gitignored) already defines `DATABASE_URL`,
  `SECRET_KEY`, and `DEBUG` and `load_dotenv()` is already called. Move settings onto the env
  vars rather than adding more literals.
- `README.md` describes GitHub Actions CI/CD and Vercel/Railway deploys as if they exist;
  no `.github/` workflows are present yet.

## Conventions

- Commit prefixes in use: `feat:` for code, `A:` for logbook/README additions.
- Work happens on `feat/*` branches off `main`; `main` is the PR target.
- After a substantive session, append to (or create) today's `.logbook/DD-Month-YYYY.md` entry —
  including the failures and the reasoning, which is the point of the journal.
