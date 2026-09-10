For deployment, I have thought for some time.


The frontend was easily deployed on Vercel without breaking a sweat. The django backend and postgres db may warrant some considerations. So far, PaaS (platform as a service) services like Railway and Render make it easy to deploy backend applications, however they have a limited 30-day free trial afterwhich your deployed applications will be rendered inactive. Moreover, even during this free trial, after 15-minute of inactivity, the deployed service will spin down and so that wouldn't be good for user experience on the other end. 

---

## How I landed on Vercel for the backend

I looked at four options before deciding. Here is what each one actually offered.

| Option | Free deal | Why I ruled it in or out |
| --- | --- | --- |
| Railway | $5 one time credit, 30 days | Everything stops once the credit is gone, app included. Would need $5 a month to stay up. |
| Render | Web service free forever, but the Postgres expires 30 days after creation | The app survives, the database does not. Also spins down after 15 minutes idle, so the first visitor waits about a minute. |
| AWS Lambda | Lambda itself has a permanent free allowance | Ruled out. Lambda gives you no database, so I would still be paying for RDS. Also needs an adapter, VPC setup, and the AWS free tier changed in July 2025 so new accounts get credits instead of 12 months free RDS. Too much AWS plumbing for a project meant to teach me Django and Vue. |
| Vercel + Neon | Both permanently free, no card | Chosen. |

### What actually decided it

Two things.

First, Vercel now has proper Django support. It finds `manage.py`, reads `WSGI_APPLICATION` out of my settings (which I already have), and runs it as a serverless function. It is not a hack.

Second, Neon. Their free Postgres plan is 0.5 GB and 100 compute hours a month, and it is permanent rather than a trial. My database is only 72 MB, so it fits with plenty of room. That kills the 30 day database clock which was the main thing making Render mediocre.

The cold start also matters. Render sleeps after 15 minutes and takes about a minute to wake. Vercel takes 300 to 800 ms. That is the difference between a link that looks broken and one that just feels slightly slow.

And the frontend is already on Vercel, so everything lives in one dashboard.

### What serverless means for my app

Serverless means nothing runs when there are no requests. A request wakes up a copy of Django, it answers, and then it dies. Fifty requests at once means fifty independent copies.

Four consequences I had to understand before committing:

1. **Cold starts.** First request after a quiet spell pays 300 to 800 ms to import Django, DRF and networkx. Everyone after that is fast.

2. **Nothing survives between requests.** Python variables are wiped every time. I got lucky here because `ScreeningCase.network_snapshot` already writes the graph into Postgres instead of holding it in memory. That is exactly the pattern serverless needs.

3. **Database connections are the real danger.** Postgres has roughly 100 connection slots. `conn_max_age=600` is correct on a normal server (2 gunicorn workers, 2 connections) but wrong on serverless, where 50 copies would each hold a connection open for 10 minutes after finishing and exhaust the slots. Fix is `conn_max_age=0` plus Neon's built in pgbouncer pooler.

4. **Management commands have nowhere to run.** No shell, no machine. `migrate` has to run from my laptop pointed at the remote database, using Neon's direct URL rather than the pooled one (DDL through pgbouncer misbehaves).

### The ingest command

`ingest_opensanctions` cannot run serverless. It streams a 2.6 GB file for about 20 minutes and a function gets seconds.

This turned out not to matter. It was never going to run in the cloud anyway, on Render either, because the 2.6 GB source file is not there and Render's free disk is ephemeral and small. What I actually do on both platforms is identical: run ingest locally, then ship the finished 72 MB up with `pg_dump` and `psql`.

The one real cost is that refreshing the sanctions data becomes a manual chore instead of something I could cron on a server. OpenSanctions updates daily and my snapshot will go stale. For a project built to learn Django and demo the graph, a snapshot from last month proves the matcher just as well, so I am accepting that.

### What still needs to change

- Change `conn_max_age` to 0 when not in DEBUG, and use Neon's pooled connection string for the app.
- Delete the `Procfile`. I wrote it for Railway and Vercel ignores it, same as Render would.
- Two separate Vercel projects, frontend from `frontend/` and backend from `backend/`. Serving both from one project fights with the SPA rewrite in `vercel.json`.
- WhiteNoise may be redundant since Vercel handles Django static files itself. Harmless to leave in for now.
- Watch the matcher. `similarity()` across 50,004 entities plus building a NetworkX graph inside a function with a hard time limit is the part most likely to bite. On a normal server a slow request is just slow. On serverless it gets killed.


https://www.google.com/search?q=free+open+source+backend+hosting+platform+for+django&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIHCAEQIRiPAjIHCAIQIRiPAtIBCTE0MTUwajBqN6gCALACAA&sourceid=chrome&ie=UTF-8&fbs=ABfTbFVyMZGZf1hfvX9uKjN_-G8cxpBkeIeqYwoCbfNVc4vKE9OqRMKGD2T9lFDfEKBBAAmW5ocR386QO4cT2Z22CGZR-lG_dnZTBDkDAZZ-sV6vXRk_cxQAFs9S8C0XCFxjJ42n3R7-P6_n8P02OnQgiQTUZuFE6r0LHQa3iCKF1dH8BepKR0DAHvylNDCKhL-3hbcxXmj0XoHWp-_ha47CwIOtpI-n8Q&aep=10&ntc=1&sxsrf=APpeQntma5Ge2RR3Ricy8-ZU_SPN7kUq0A%3A1789009995465&mstk=AUtExfB23I3HVE-KndQ_zLUgAJjFvy1qV4r63hPPITH2Hy-ZnPWCfRZV4jblQeoXc0lG8HyCMPhui8GtcdZx7Ehl_SIv1mlXGh0v922kJU5fc1kz6CgNLRbF38P2qiEsu7jRooMKMFwqNP7J4xBXynH2TYHFaL4rxXwrjVDaw9rpqSEf1rbaEcu6qU_O1RGanm3CFlbBgZRovf1q0AhCDX3cKjPiDRgXJb675a3fsVQl6wB4_eWmdTb5Kerd6lJuJ6GAsPyfDeT8gAinSCLZkY1lm1-xeFzpAa6N_9WTSwbRYPWro96-6PR2lVe_C26grIJN-KuiykQHOrPTFfztKWimFYXXJlBqt9ItuWHq7rHgHbXdwtfbMZBRKMUvADza5xbdhAdl6aNt7joP&aioh=3&csuir=1&cs=1&udm=50&atvm=2&mtid=0CGiaumXDciaseMPs7mywQg

---

## Deployed it. What actually happened.

The plan above was mostly right, but two things went differently and both cost me a debugging cycle.

### The database side went smoothly

Created a Neon project (`sanctions-graph`, AWS Asia Pacific 2 Sydney, Postgres on, Neon Auth off). Free plan gives 0.5 GB storage and 100 CU-hours a month and it is permanent, not a trial. My data is 72 MB so there is plenty of room.

Neon gives two connection strings and the only difference is `-pooler` in the hostname:

```
DIRECT  ep-xxxx.ap-southeast-2.aws.neon.tech           for migrate and the data restore
POOLED  ep-xxxx-pooler.ap-southeast-2.aws.neon.tech    for Vercel (DATABASE_URL)
```

I saved both into `backend/.env.neon`, which `.gitignore` already covers via `.env*`.

First gotcha: my Neon password contains a `&`, and sourcing the file blew up with `parse error near '&'` because zsh reads an unquoted `&` as the background operator. Fix was wrapping both values in single quotes. Single, not double, so nothing gets expanded.

Then:

```bash
cd backend
set -a; source .env.neon; set +a
DEBUG=False DATABASE_URL="$NEON_DIRECT_URL" uv run manage.py migrate
```

22 migrations applied. Verified `pg_trgm` actually installed rather than silently skipped:

```bash
docker exec -i sg-postgres psql "$NEON_DIRECT_URL" -c "SELECT extname FROM pg_extension;"
```

`plpgsql` and `pg_trgm`. Worth checking because the entire matcher is `similarity()`.

### Copying the data, and why the order matters

I dumped in three files instead of one, because `pg_dump` emits tables in alphabetical order, not the order I list them with `-t`. Alphabetically the children come before the parent, so a single dump would have failed on a foreign key violation.

```
1_parents.sql   agent, sanctionedentity                                nothing points at these
2_children.sql  entityaddress, entityalias, entityidentifier, screeningcase
3_matches.sql   match                                                   points at case AND entity
```

Restored with `psql -v ON_ERROR_STOP=1` so it halts instead of leaving me with half the data. 17 MB of dumps for 72 MB on disk, because indexes are not dumped, they get rebuilt from the migrations.

Second thing I was told wrong: I was warned I would need to reset the id sequences manually or the first insert would collide on a duplicate primary key. Turns out `pg_dump --data-only` includes the `setval` calls itself. The output showed a `setval` after every `COPY`. No manual step needed.

Final counts on Neon: 8 agents, 50,004 entities, 90,945 addresses, 26,735 aliases, 40,868 identifiers, 8 cases, 270 matches.

Sanity check that the matcher would work against the real data:

```sql
SELECT round(similarity(name, 'Sergey Lavrov')::numeric, 3), name
FROM screening_sanctionedentity
WHERE similarity(name, 'Sergey Lavrov') > 0.6;
```

Returned `Sergei Lavrov` at 0.750. Above my 0.6 threshold. Also a reminder of why I lowered it from 0.7, since the Putin typo case sits at 0.667.

I did not copy `auth_user`, so I ran `createsuperuser` again against Neon. Same username, different and stronger password, because this one is reachable from the internet.

### The Vercel side is where it went wrong

Two failures in a row.

**Failure 1: `vercel.json` killed the build before it started.**

```
Error: The pattern "sanctionsgraph/wsgi.py" defined in `functions`
doesn't match any Serverless Functions inside the `api` directory.
```

The `functions` key in `vercel.json` only accepts paths inside an `api/` folder. Django on Vercel is framework detected and Vercel generates the function itself, so no path prefix would have fixed it. The key simply does not apply. Deleted the file. `maxDuration` belongs in Project Settings instead.

**Failure 2: a build that "succeeded" in 58 milliseconds and produced nothing.**

```
Build Completed in /vercel/output [58ms]
Skipping cache upload because no files were prepared
```

Every route returned Vercel's own branded `404: NOT_FOUND`, which is different from Django's plain `Not Found` page. That difference is the tell: Vercel's version means no function matched at the platform level, so Django was never even reached.

The cause was that the **Framework Preset** was not actually set to Django on the project, even though the import screen showed a `Django` badge next to the `backend` folder. Setting Settings > Build and Deployment > Framework Preset to Django and redeploying fixed it.

I was also told to commit a `requirements.txt` because the preset's Install Command placeholder says `pip install -r requirements.txt`. That turned out to be unnecessary. The working build log says:

```
Using Python 3.12 from backend/.python-version
Using uv 0.10.11
Installing required dependencies from uv.lock
Django 6.1.1 detected
Running collectstatic...
Build Completed in /vercel/output [7s]
```

It reads `uv.lock` natively. My instinct to let Vercel use uv instead of generating a requirements file was right. Removed the file again in a follow up commit.

### Environment variables

Backend project (`sanctions-graph-api`, Root Directory `backend`):

```
DEBUG                 False
SECRET_KEY            generated fresh, marked Secret
DATABASE_URL          the POOLED Neon url, marked Secret
ALLOWED_HOSTS         .vercel.app
CSRF_TRUSTED_ORIGINS  https://sanctions-graph-api.vercel.app
CORS_ALLOWED_ORIGINS  https://sanctions-graph.vercel.app
```

The leading dot in `.vercel.app` is Django's subdomain wildcard, which covers preview deployments too. Without it every preview URL returns 400.

Frontend project (`sanctions-graph`, Root Directory `frontend`):

```
VITE_API_BASE_URL     https://sanctions-graph-api.vercel.app/api
```

Vercel refused to let me mark this one as Secret, and it was right to. Anything with a `VITE_` prefix gets baked into the JavaScript bundle at build time, so it is downloaded by every visitor and readable in DevTools. Marking it secret would only hide it from me while still publishing it. Set it to Config instead. Real secrets never get the `VITE_` prefix.

Also worth remembering: Vite bakes env vars in at build time, so changing the variable does nothing on its own. It needs a redeploy.

### Verified

```
frontend  GET /cases       200
backend   GET /api/cases/  200, real Neon data
CORS from https://sanctions-graph.vercel.app  -> access-control-allow-origin present
CORS from https://evil.example.com            -> no header, correctly refused
x-vercel-id: syd1::syd1::                     -> function running in Sydney, next to the database
```

`/admin/` renders fully styled, which proves `collectstatic` and static serving from the CDN both work.

Region pairing mattered here. Vercel builds in `iad1` (Washington) but the function region is separate. If the function had stayed in Washington while Neon sits in Sydney, every query would cross the Pacific at roughly 200 ms, and my matcher makes several queries per screening. It ended up in `syd1` next to the database.

### The thing I must not forget: migrations

There is no shell on Vercel, so `manage.py` cannot run there. Migrations have to run from my laptop against Neon, and they have to run **before** merging to main, not after. Merging first deploys code that expects columns the database does not have yet.

```bash
cd backend
set -a; source .env.neon; set +a
DEBUG=False DATABASE_URL="$NEON_DIRECT_URL" uv run manage.py migrate
```

Use the DIRECT url, not the pooled one. `CREATE TABLE` and `CREATE EXTENSION` are DDL and pgbouncer pools per transaction, so DDL through the pooler misbehaves.

Same pattern for anything else that touches the live database:

```bash
DEBUG=False DATABASE_URL="$NEON_DIRECT_URL" uv run manage.py createsuperuser
DEBUG=False DATABASE_URL="$NEON_DIRECT_URL" uv run manage.py shell
```

Without the `DATABASE_URL` prefix these all hit my local docker container instead, because `settings.py` falls back to `postgres://sguser:sgpass@localhost:5432/sanctionsgraph`. That fallback is deliberate so local development and pytest are unaffected.

New deploy checklist, in order:

1. Write the migration locally and run it against docker.
2. Run it against Neon with the DIRECT url.
3. Then merge to main, which triggers the production deploy.

### Where it stands

All three tiers are free with no 30-day clock, which was the whole reason for picking this over Railway and Render.

```
sanctions-graph.vercel.app      Vue on the CDN
        |
sanctions-graph-api.vercel.app  Django function, syd1, scales to zero
        |
Neon Postgres, Sydney           208,930 rows, 72 MB of 0.5 GB, pg_trgm on
```

Still to watch: the matcher inside a function with a hard time limit. Case 6 with its 128 Hong Kong matches is the one that will find that limit first.
