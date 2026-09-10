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