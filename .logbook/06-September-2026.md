### Person record

```bash
{
    "id": "NK-224TRezPqwzhQZ37exWxtX",        ← source_id (OpenSanctions UUID)
    "caption": "SANAVBARI NIKITENKO",          ← display name
    "schema": "Person",                         ← entity_type in our model
    "properties": {
        "name": ["SANAVBARI NIKITENKO"],       ← primary name (list, even if one item)
        "firstName": ["SANAVBARI"],            ← given name
        "lastName": ["NIKITENKO"],             ← family name
        "birthDate": ["1992-06-28"],           ← date of birth
        "nationality": ["ru"],                 ← country code
        "country": ["tj"],                     ← country of record
        "gender": ["female"],                  ← gender
        "topics": ["wanted", "crime"]          ← tags (sanction, wanted, crime, etc.)
    },
    "target": true                             ← true = this person IS sanctioned/wanted
}
```


### Company record


```bash
{
    "id": "NK-223CQDBzp8MRkdJMDiqXn3",
    "caption": "Myanmar Yatai International Holding Group Co., LTD.",
    "schema": "Company",
    "referents": [
        "usgsa-s4mrwvjp8",
        "ofac-pr-1ab25d5e07869a9c0a738572f2a65264c903e13e",
        "usgsa-s4mrxdbkr",
        "usgsa-s4mrxdbks",
        "usgsa-375a498d889ec895144ff360bf263a0409dcd68d",
        "ofac-pr-e48470d757db9b4d055d5250704db04af0096375",
        "permid-5087304836",
        "oc-companies-mm-1fc-2016-2017-kyn",
        "ofac-pr-eeb375713cf08ae562a6c803379026faec3559b2",
        "ofac-pr-6ad9ad0a10350419f24b0794dbe9f530abd81b59",
        "usgsa-505d34fb86b92d2eaa597594eb50bbc7d2316f02",
        "usgsa-db0c3a9f714e8018701a676253d208fde23424e7",
        "usgsa-s4mrxdbkq",
        "usgsa-233e6cb3df9bae423e436306e0cad70b4bb33b6c",
        "ofac-54742"
    ],
    "datasets": [
        "us_sam_exclusions",
        "us_ofac_sdn",
        "ext_us_ofac_press_releases",
        "opencorporates",
        "permid",
        "us_trade_csl"
    ],
    "origin": [
        "metadata",
        "gpt-4o",
        "inferred"
    ],
    "first_seen": "2025-09-08T14:10:01",
    "last_seen": "2026-09-05T06:53:02",
    "last_change": "2026-09-02T02:22:05",
    "properties": {
        "sourceUrl": [
            "https://sanctionssearch.ofac.treas.gov/Details.aspx?id=54742",
            "https://home.treasury.gov/news/press-releases/sb0237",
            "https://permid.org/1-5087304836"
        ],
        "name": [
            "Myanmar Yatai International Holding Group Company Ltd",
            "YATAI NEW CITY",
            "YATAI SMART INDUSTRIAL NEW CITY",
            "SHWE KOKKO SPECIAL ECONOMIC ZONE",
            "Myanmar Yatai International Holding Group Co., LTD.",
            "Myanmar Yatai International Holding Group Co., Ltd"
        ],
        "opencorporatesUrl": [
            "https://opencorporates.com/companies/mm/1FC-2016-2017(KYN)"
        ],
        "status": [
            "Active"
        ],
        "permId": [
            "5087304836"
        ],
        "jurisdiction": [
            "mm"
        ],
        "incorporationDate": [
            "2017-02-14"
        ],
        "alias": [
            "Yatai Smart Industrial New City",
            "Yatai New City",
            "Shwe Kokko Special Economic Zone"
        ],
        "sector": [
            "Construction of buildings"
        ],
        "registrationNumber": [
            "103919088"
        ],
        "country": [
            "mm"
        ],

```


### Comparision between the two records
| Field                                | In Person                        | In Company                                             | What we do with it                     |
| ------------------------------------ | -------------------------------- | ------------------------------------------------------ | -------------------------------------- |
| `name`                               | `["SANAVBARI NIKITENKO"]`        | `["Myanmar Yatai...", "YATAI NEW CITY", ...]`          | Primary name → `SanctionedEntity.name` |
| `alias`                              | **Not present**                  | `["Yatai Smart Industrial...", "Yatai New City", ...]` | Aliases → `EntityAlias`                |
| `address`                            | **Not present** (in that Person) | `["HPA-AN CITY", "Shwe Kokko Village..."]`             | Addresses → `EntityAddress`            |
| `registrationNumber`                 | **Not present**                  | `["103919088"]`                                        | Identifier → `EntityIdentifier`        |
| `innCode` / `ogrnCode` / `taxNumber` | Sometimes present                | Often present                                          | Identifiers → `EntityIdentifier`       |
| `country`                            | `["tj"]`                         | `["mm"]`                                               | We store it but do not index heavily   |
| `incorporationDate`                  | N/A                              | `["2017-02-14"]`                                       | Not stored in MVP (skip it)            |


<b>Key insight</b>:
 
The properties structure is the same shape for both Person and Company, but the keys inside differ. Our ingestion script must handle:
- name list (always present)
- alias list (sometimes present)
- address list (sometimes present)
- Various identifier keys: passportNumber, taxNumber, idNumber, registrationNumber, innCode, ogrnCode, npiCode, leiCode




For my future self, since I will need postgresql up and running constantly, I will need to run the following command before starting the server


```bash
uv run manage.py dbshell
``` 


# Server would not start: connection refused

Came back to the project later in the day, ran `uv run manage.py runserver` and it blew up
before serving anything:

```bash
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
        Is the server running on that host and accepting TCP/IP connections?
```

The cause was boring in the end. The `sg-postgres` container had stopped. It had been up since
yesterday and died at 10:35 UTC with exit code 255, and the container log showed
`database system was not properly shut down; automatic recovery in progress`, so Docker Desktop
went down and took the container with it. Postgres replayed its WAL on the next start and
recovered fine, nothing was lost.

Worth writing down that this is NOT the same problem as yesterday. Yesterday I got
`password authentication failed`, which meant something *was* listening on 5432 and rejecting
`sguser` (the native postgres service). Today was `connection refused`, which means nothing was
listening at all. Opposite causes, so "check port occupancy" does not help here.

The reason `runserver` dies instead of just booting without a database is that it calls
`check_migrations()` on startup, which reads the `django_migrations` table to see if anything is
unapplied. That needs a live connection. In `runserver.py` that call sits outside the
`skip_checks` guard, so there is no flag to skip it. Postgres has to be up first, always.

# Fix

The container already exists, so it is `docker start`, not `docker run` again (that would just
fail on the name conflict):

```bash
docker start sg-postgres
docker ps                       # want to see "Up X seconds" and 0.0.0.0:5432->5432/tcp
uv run manage.py runserver
```

So the note I left above about running `docker run ...` is only right the very first time. Every
session after that it is `docker start sg-postgres`.

# TODO

The container has no restart policy (`RestartPolicy: no`), which is why it never came back on its
own. This will happen again every time Docker Desktop restarts. Fix it with:

```bash
docker update --restart unless-stopped sg-postgres
```

Have not run this yet.



```bash
uv run manage.py ingest_opensanctions --limit 5000
Processed 1,000 entities...
Processed 2,000 entities...
Processed 3,000 entities...
Processed 4,000 entities...
Processed 5,000 entities...
Ingestion complete.
  Entities created: 5,000
  Aliases created: 2,566
  Addresses created: 9,016
  Identifiers created: 4,055
  Skipped (schema not screened): 8,738
  Skipped (no name): 0
  Skipped (already ingested): 0
  Unparseable lines: 0
                                                                                                                                           
uv run manage.py ingest_opensanctions --limit 50000
Processed 1,000 entities...
Processed 2,000 entities...
Processed 3,000 entities...
Processed 4,000 entities...
Processed 5,000 entities...
Processed 6,000 entities...
Processed 7,000 entities...
Processed 8,000 entities...
Processed 9,000 entities...
Processed 10,000 entities...
Processed 11,000 entities...
Processed 12,000 entities...
Processed 13,000 entities...
Processed 14,000 entities...
Processed 15,000 entities...
Processed 16,000 entities...
Processed 17,000 entities...
Processed 18,000 entities...
Processed 19,000 entities...
Processed 20,000 entities...
Processed 21,000 entities...
Processed 22,000 entities...
Processed 23,000 entities...
Processed 24,000 entities...
Processed 25,000 entities...
Processed 26,000 entities...
Processed 27,000 entities...
Processed 28,000 entities...
Processed 29,000 entities...
Processed 30,000 entities...
Processed 31,000 entities...
Processed 32,000 entities...
Processed 33,000 entities...
Processed 34,000 entities...
Processed 35,000 entities...
Processed 36,000 entities...
Processed 37,000 entities...
Processed 38,000 entities...
Processed 39,000 entities...
Processed 40,000 entities...
Processed 41,000 entities...
Processed 42,000 entities...
Processed 43,000 entities...
Processed 44,000 entities...
Processed 45,000 entities...
Processed 46,000 entities...
Processed 47,000 entities...
Processed 48,000 entities...
Processed 49,000 entities...
Processed 50,000 entities...
Ingestion complete.
  Entities created: 45,000
  Aliases created: 24,166
  Addresses created: 81,925
  Identifiers created: 36,813
  Skipped (schema not screened): 89,053
  Skipped (no name): 7
  Skipped (already ingested): 5,000
  Unparseable lines: 0
```                                                                                                                                           
