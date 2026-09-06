I continued to work on the scaffolding of the frontend by creating useful folders to be used later:

```bash 
views
constants
types
```


I set up PostgreSQL via docker with the following command


```bash 
docker run -d \
  --name sg-postgres \
  -e POSTGRES_USER=sguser \
  -e POSTGRES_PASSWORD=sgpass \
  -e POSTGRES_DB=sanctionsgraph \
  -p 5432:5432 \
  postgres:15
```

and verified that it ran by doing:

```bash 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ docker ps
CONTAINER ID   IMAGE         COMMAND                  CREATED          STATUS          PORTS                                         NAMES
9efeb6eefa18   postgres:15   "docker-entrypoint.s…"   15 minutes ago   Up 15 minutes   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp   sg-postgres   
```


Then I tried to configure Django to connect to that particular PostgreSQL container on `localhost:5432`, but `migrate` threw a `password authentication fialed for user "sguser"` error. 


<details>
    ~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ docker logs sg-postgres
The files belonging to this database system will be owned by user "postgres".
This user must also own the server process.

The database cluster will be initialized with locale "en_US.utf8".
The default database encoding has accordingly been set to "UTF8".
The default text search configuration will be set to "english".

Data page checksums are disabled.

fixing permissions on existing directory /var/lib/postgresql/data ... ok
creating subdirectories ... ok
selecting dynamic shared memory implementation ... posix
selecting default max_connections ... 100
selecting default shared_buffers ... 128MB
selecting default time zone ... Etc/UTC
creating configuration files ... ok
running bootstrap script ... ok
performing post-bootstrap initialization ... ok
initdb: warning: enabling "trust" authentication for local connections
initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
syncing data to disk ... ok
Success. You can now start the database server using:

    pg_ctl -D /var/lib/postgresql/data -l logfile start

waiting for server to start....2026-09-05 05:44:28.073 UTC [48] LOG:  starting PostgreSQL 15.19 (Debian 15.19-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
2026-09-05 05:44:28.077 UTC [48] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-09-05 05:44:28.089 UTC [51] LOG:  database system was shut down at 2026-09-05 05:44:27 UTC
2026-09-05 05:44:28.097 UTC [48] LOG:  database system is ready to accept connections
 done
server started
CREATE DATABASE
/usr/local/bin/docker-entrypoint.sh: ignoring /docker-entrypoint-initdb.d/*

waiting for server to shut down...2026-09-05 05:44:28.301 UTC [48] LOG:  received fast shutdown request
.2026-09-05 05:44:28.306 UTC [48] LOG:  aborting any active transactions
2026-09-05 05:44:28.308 UTC [48] LOG:  background worker "logical replication launcher" (PID 54) exited with exit code 1
2026-09-05 05:44:28.308 UTC [49] LOG:  shutting down
2026-09-05 05:44:28.311 UTC [49] LOG:  checkpoint starting: shutdown immediate
2026-09-05 05:44:28.404 UTC [49] LOG:  checkpoint complete: wrote 922 buffers (5.6%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.016 s, sync=0.070 s, total=0.096 s; sync files=301, longest=0.004 s, average=0.001 s; distance=4239 kB, estimate=4239 kB
2026-09-05 05:44:28.409 UTC [48] LOG:  database system is shut down
 done
server stopped

PostgreSQL init process complete; ready for start up.

2026-09-05 05:44:28.524 UTC [1] LOG:  starting PostgreSQL 15.19 (Debian 15.19-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
2026-09-05 05:44:28.524 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-09-05 05:44:28.524 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-09-05 05:44:28.529 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-09-05 05:44:28.537 UTC [64] LOG:  database system was shut down at 2026-09-05 05:44:28 UTC
2026-09-05 05:44:28.543 UTC [1] LOG:  database system is ready to accept connections
2026-09-05 05:49:28.604 UTC [62] LOG:  checkpoint starting: time
2026-09-05 05:49:31.455 UTC [62] LOG:  checkpoint complete: wrote 44 buffers (0.3%); 0 WAL file(s) added, 0 removed, 0 recycled; write=2.837 s, sync=0.006 s, total=2.852 s; sync files=12, longest=0.003 s, average=0.001 s; distance=252 kB, estimate=252 kB
                                                                               
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ sudo lsof -i :5432
[sudo] password for sething2002: 
COMMAND  PID     USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
postgres 431 postgres    5u  IPv4  13473      0t0  TCP localhost:postgresql (LISTEN)
                                                                               
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ sudo systemctl disable postgresql
Synchronizing state of postgresql.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install disable postgresql
Removed /etc/systemd/system/multi-user.target.wants/postgresql.service.
                                                                               
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ uv run manage.py migrate         
Traceback (most recent call last):
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/lib/python3.12/site-packages/django/db/backends/base/base.py", line 279, in ensure_connection
    self.connect()
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/lib/python3.12/site-packages/django/utils/asyncio.py", line 26, in inner
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/lib/python3.12/site-packages/django/db/backends/base/base.py", line 256, in connect
    self.connection = self.get_new_connection(conn_params)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/lib/python3.12/site-packages/django/utils/asyncio.py", line 26, in inner
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/lib/python3.12/site-packages/django/db/backends/postgresql/base.py", line 345, in get_new_connection
    connection = self.Database.connect(**conn_params)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: FATAL:  password authentication failed for user "sguser"
connection to server at "localhost" (127.0.0.1), port 5432 failed: FATAL:  password authentication failed for user "sguser"


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/manage.py", line 22, in <module>
    main()
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/manage.py", line 18, in main

                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: FATAL:  password authentication failed for user "sguser"
connection to server at "localhost" (127.0.0.1), port 5432 failed: FATAL:  password authentication failed for user "sguser"
</details>



The container logs looked healthy:


```bash
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ docker logs sg-postgres
The files belonging to this database system will be owned by user "postgres".
This user must also own the server process.

The database cluster will be initialized with locale "en_US.utf8".
The default database encoding has accordingly been set to "UTF8".
The default text search configuration will be set to "english".

Data page checksums are disabled.

fixing permissions on existing directory /var/lib/postgresql/data ... ok
creating subdirectories ... ok
selecting dynamic shared memory implementation ... posix
selecting default max_connections ... 100
selecting default shared_buffers ... 128MB
selecting default time zone ... Etc/UTC
creating configuration files ... ok
running bootstrap script ... ok
performing post-bootstrap initialization ... ok
initdb: warning: enabling "trust" authentication for local connections
initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
syncing data to disk ... ok


Success. You can now start the database server using:

    pg_ctl -D /var/lib/postgresql/data -l logfile start

waiting for server to start....2026-09-05 05:44:28.073 UTC [48] LOG:  starting PostgreSQL 15.19 (Debian 15.19-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
2026-09-05 05:44:28.077 UTC [48] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-09-05 05:44:28.089 UTC [51] LOG:  database system was shut down at 2026-09-05 05:44:27 UTC
2026-09-05 05:44:28.097 UTC [48] LOG:  database system is ready to accept connections
 done
server started
CREATE DATABASE


/usr/local/bin/docker-entrypoint.sh: ignoring /docker-entrypoint-initdb.d/*

waiting for server to shut down...2026-09-05 05:44:28.301 UTC [48] LOG:  received fast shutdown request
.2026-09-05 05:44:28.306 UTC [48] LOG:  aborting any active transactions
2026-09-05 05:44:28.308 UTC [48] LOG:  background worker "logical replication launcher" (PID 54) exited with exit code 1
2026-09-05 05:44:28.308 UTC [49] LOG:  shutting down
2026-09-05 05:44:28.311 UTC [49] LOG:  checkpoint starting: shutdown immediate
2026-09-05 05:44:28.404 UTC [49] LOG:  checkpoint complete: wrote 922 buffers (5.6%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.016 s, sync=0.070 s, total=0.096 s; sync files=301, longest=0.004 s, average=0.001 s; distance=4239 kB, estimate=4239 kB
2026-09-05 05:44:28.409 UTC [48] LOG:  database system is shut down
 done
server stopped

PostgreSQL init process complete; ready for start up.

2026-09-05 05:44:28.524 UTC [1] LOG:  starting PostgreSQL 15.19 (Debian 15.19-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
2026-09-05 05:44:28.524 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-09-05 05:44:28.524 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-09-05 05:44:28.529 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-09-05 05:44:28.537 UTC [64] LOG:  database system was shut down at 2026-09-05 05:44:28 UTC
2026-09-05 05:44:28.543 UTC [1] LOG:  database system is ready to accept connections
2026-09-05 05:49:28.604 UTC [62] LOG:  checkpoint starting: time
2026-09-05 05:49:31.455 UTC [62] LOG:  checkpoint complete: wrote 44 buffers (0.3%); 0 WAL file(s) added, 0 removed, 0 recycled; write=2.837 s, sync=0.006 s, total=2.852 s; sync files=12, longest=0.003 s, average=0.001 s; distance=252 kB, estimate=252 kB
                                              
```


So the most likely cause was that there was another postgres instance bound to port `5432` already running on my machine (apparently at PID 431). The host OS was routing Django's connection to the native instance, which did not know the `sguser` account.


# Fix 
I stopped the native service (sudo systemctl stop postgresql), but the existing container still refused connections from the host because its port binding was initialized during the conflict. I destroyed the container (docker rm -f sg-postgres) and recreated it with a clean port mapping. Django connected immediately and migrations ran.


# The Lesson

Always verify port occupancy before creating containers. A port conflict can manifest as an authentication error because the wrong service answers the request.




--------

```zsh
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ uv run manage.py makemigrations screening

Migrations for 'screening':
  screening/migrations/0001_initial.py
    + Create model Agent
    + Create model SanctionedEntity
    + Create model ScreeningCase
    + Create model Match
    + Create model EntityIdentifier
    + Create model EntityAlias
    + Create model EntityAddress
                                                                               
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ uv run manage.py migrate

Operations to perform:
  Apply all migrations: admin, auth, contenttypes, screening, sessions
Running migrations:
  Applying screening.0001_initial... OK

~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ uv run manage.py dbshell
psql (14.24 (Ubuntu 14.24-0ubuntu0.22.04.1), server 15.19 (Debian 15.19-1.pgdg13+2))
WARNING: psql major version 14, server major version 15.
         Some psql features might not work.
Type "help" for help.

sanctionsgraph=# \d screening_agent

   Column    |           Type           | Collation | Nullable |             Default              
-------------+--------------------------+-----------+----------+----------------------------------
 id          | bigint                   |           | not null | generated by default as identity
 name        | character varying(255)   |           | not null | 
 aliases     | jsonb                    |           | not null |
 birth_date  | date                     |           |          | 
 nationality | character varying(2)     |           | not null | 
 created_at  | timestamp with time zone |           | not null | 
Indexes:
    "screening_agent_pkey" PRIMARY KEY, btree (id)
    "screening_agent_name_c53f9a5b" btree (name)
    "screening_agent_name_c53f9a5b_like" btree (name varchar_pattern_ops)
Referenced by:
    TABLE "screening_screeningcase" CONSTRAINT "screening_screeningcase_agent_id_cfb178ff_fk_screening_agent_id" FOREIGN KEY (agent_id) REFERENCES screening_agent(id) DEFERRABLE INITIALLY DEFERRED

```


After setting up the scaffolding for the frontend and backend, I need to seed the sanction records table in postgresql. And so I had a look into the following resources

1. [Opensanctions docs](https://www.opensanctions.org/docs/entities/)
2. [Financial crimes](https://www.youtube.com/watch?v=qiSopTTmBI4&pp=ygUQZmluYW5jaWFsIGNyaW1lcw%3D%3D)
3. [Podcast episode between neo4j and Fridrich Lindenburg](https://www.youtube.com/watch?v=T3uGVrrMeTo&t=758s&pp=ygUNb3BlbnNhY250aW9ucw%3D%3D)
4. [Another talk between Fridrich & Jean Villedieu](https://www.youtube.com/watch?v=zuIeC72IwL0&t=309s&pp=ygUNb3BlbnNhY250aW9ucw%3D%3D)


```bash 
~/personal-projects/VueDjango/sanctions-graph 
└─❯ wget -O backend/data/entities.ftm.json https://data.opensanctions.org/datasets/latest/default/entities.ftm.json
--2026-09-05 21:46:27--  https://data.opensanctions.org/datasets/latest/default/entities.ftm.json
```


