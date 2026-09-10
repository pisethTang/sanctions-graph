```bash
~/personal-projects/VueDjango/sanctions-graph 
└─❯ cd backend 
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ uv run manage.py runserver
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
September 10, 2026 - 03:30:20
Django version 6.1.1, using settings 'sanctionsgraph.settings'
Starting WSGI development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.

WARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.
For more information on production servers see: https://docs.djangoproject.com/en/6.1/howto/deployment/
/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/sanctionsgraph/settings.py changed, reloading.
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
September 10, 2026 - 04:44:50
Django version 6.1.1, using settings 'sanctionsgraph.settings'
Starting WSGI development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.

WARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.
For more information on production servers see: https://docs.djangoproject.com/en/6.1/howto/deployment/
^C source /home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/bin/activate
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯  source /home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/bin/activate
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ cd ..
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git add .
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git rm --cached backend/Profile 2>/dev/null || true
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git commit -m "feat: make backend deployable to Vercel with Neon Postgres"
[feat/deploy-vercel 0a5d567] feat: make backend deployable to Vercel with Neon Postgres
 9 files changed, 229 insertions(+), 24 deletions(-)
 create mode 100644 .claude/flagged_speech_patterns.md
 create mode 100644 .claude/skills/full_review/SKILL.md
 create mode 100644 .claude/skills/grill_me/SKILL.md
 create mode 100644 .logbook/09-September-2026.md
 create mode 100644 backend/vercel.json
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git push -u origin feat/deploy-vercel
Enumerating objects: 26, done.
Counting objects: 100% (26/26), done.
Delta compression using up to 16 threads
Compressing objects: 100% (16/16), done.
Writing objects: 100% (18/18), 8.73 KiB | 2.18 MiB/s, done.
Total 18 (delta 7), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (7/7), completed with 7 local objects.
remote: 
remote: Create a pull request for 'feat/deploy-vercel' on GitHub by visiting:
remote:      https://github.com/pisethTang/sanctions-graph/pull/new/feat/deploy-vercel
remote: 
To https://github.com/pisethTang/sanctions-graph
 * [new branch]      feat/deploy-vercel -> feat/deploy-vercel
Branch 'feat/deploy-vercel' set up to track remote branch 'feat/deploy-vercel' from 'origin'.
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ gh pr create --base main --title "feat: deploy Django backend to Vercel" \
  --body "Adds dj-database-url, whitenoise and a serverless-safe database config (conn_max_age=0, disable_server_side_cursors, sslmode=require). Moves ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS and CORS_ALLOWED_ORIGINS onto env vars with local defaults unchanged. Adds vercel.json with maxDuration 60 for the matcher. Drops the Railway Procfile. 101 tests passing.

"                                                               

Creating pull request for feat/deploy-vercel into main in pisethTang/sanctions-graph

https://github.com/pisethTang/sanctions-graph/pull/11
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ gh pr merge --merge
✓ Merged pull request pisethTang/sanctions-graph#11 (feat: deploy Django backend to Vercel)
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git checkout main
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
                                                                                      
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git pull
Updating 8b9361f..8eeac16
Fast-forward
 .claude/flagged_speech_patterns.md  | 10 ++
 .claude/skills/full_review/SKILL.md | 34 +++++++
 .claude/skills/grill_me/SKILL.md    |  7 ++
 .gitignore                          |  4 +-
 .logbook/09-September-2026.md       | 62 ++++++++++++
 backend/pyproject.toml              |  3 +
 backend/sanctionsgraph/settings.py  | 89 ++++++++++++-----
 backend/uv.lock                     | 36 +++++++
 backend/vercel.json                 |  8 ++
 9 files changed, 229 insertions(+), 24 deletions(-)
 create mode 100644 .claude/flagged_speech_patterns.md
 create mode 100644 .claude/skills/full_review/SKILL.md
 create mode 100644 .claude/skills/grill_me/SKILL.md
 create mode 100644 .logbook/09-September-2026.md
 create mode 100644 backend/vercel.json
                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph 
└─❯ cd /home/sething2002/personal-projects/VueDjango/sanctions-graph/backend
set -a; source .env.neon; set +a
echo "direct host: $(echo $NEON_DIRECT_URL | sed 's|.*@||; s|/.*||')"
echo "pooled host: $(echo $NEON_POOLED_URL | sed 's|.*@||; s|/.*||')"

.env.neon:1: parse error near `&'
direct host: 
pooled host: 
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ cd /home/sething2002/personal-projects/VueDjango/sanctions-graph/backend
set -a; source .env.neon; set +a
echo "direct host: $(echo $NEON_DIRECT_URL | sed 's|.*@||; s|/.*||')"
echo "pooled host: $(echo $NEON_POOLED_URL | sed 's|.*@||; s|/.*||')"

direct host: ep-steep-base-a7mvag96.ap-southeast-2.aws.neon.tech
pooled host: ep-steep-base-a7mvag96-pooler.ap-southeast-2.aws.neon.tech
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ DEBUG=False DATABASE_URL="$NEON_DIRECT_URL" uv run manage.py migrate

Operations to perform:
  Apply all migrations: admin, auth, contenttypes, screening, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying screening.0001_initial... OK
  Applying screening.0002_alter_entityidentifier_id_type... OK
  Applying screening.0003_agent_addresses_trigram... OK
  Applying screening.0004_alter_sanctionedentity_id... OK
  Applying screening.0005_sanctionedentity_is_target_alter_agent_id... OK
  Applying sessions.0001_initial... OK
                                                                                                                                 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ docker exec -i sg-postgres psql "$NEON_DIRECT_URL" -c "SELECT extname FROM pg_extension;"

 extname 
---------
 plpgsql
 pg_trgm
(2 rows)

                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ >....                                                                                                                                                                            

docker exec sg-postgres pg_dump -U sguser -d sanctionsgraph \
  --data-only --no-owner --no-acl \
  -t screening_match \
  > /tmp/3_matches.sql

ls -lh /tmp/1_parents.sql /tmp/2_children.sql /tmp/3_matches.sql

Permissions Size User        Date Modified Name
.rw-r--r--  5.3M sething2002 10 Sep 15:11   /tmp/1_parents.sql
.rw-r--r--   12M sething2002 10 Sep 15:11   /tmp/2_children.sql
.rw-r--r--   44k sething2002 10 Sep 15:11   /tmp/3_matches.sql
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ grep '^COPY' /tmp/1_parents.sql /tmp/2_children.sql /tmp/3_matches.sql | cut -c1-80

/tmp/1_parents.sql:COPY public.screening_agent (id, name, aliases, birth_date, n
/tmp/1_parents.sql:COPY public.screening_sanctionedentity (id, name, entity_type
/tmp/2_children.sql:COPY public.screening_entityaddress (id, street, city, posta
/tmp/2_children.sql:COPY public.screening_entityalias (id, text, language, entit
/tmp/2_children.sql:COPY public.screening_entityidentifier (id, id_type, value_h
/tmp/2_children.sql:COPY public.screening_screeningcase (id, risk_score, status,
/tmp/3_matches.sql:COPY public.screening_match (id, match_type, confidence, expl
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ >....                                                                                                                                                                            
    screening_entityaddress    ─┐
    screening_entityalias      ─┤ all point at sanctionedentity
    screening_entityidentifier ─┘   ✔ already loaded in file 1
    screening_screeningcase    ──► points at agent  ✔ already loaded

  3_matches.sql
    screening_match ──► points at screeningcase ✔ and sanctionedentity ✔

∙ 
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ docker exec -i sg-postgres psql "$NEON_DIRECT_URL" -v ON_ERROR_STOP=1 < /tmp/1_parents.sql
docker exec -i sg-postgres psql "$NEON_DIRECT_URL" -v ON_ERROR_STOP=1 < /tmp/2_children.sql
docker exec -i sg-postgres psql "$NEON_DIRECT_URL" -v ON_ERROR_STOP=1 < /tmp/3_matches.sql

SET
SET
SET
SET
SET
 set_config 
------------
 
(1 row)

SET
SET
SET
SET
COPY 8
COPY 50004
 setval 
--------
      8
(1 row)

 setval 
--------
  50004
(1 row)

SET
SET
SET
SET
SET
 set_config 
------------
 
(1 row)

SET
SET
SET
SET
COPY 90945
COPY 26735
COPY 40868
COPY 8
 setval 
--------
  90945
(1 row)

 setval 
--------
  26735
(1 row)

 setval 
--------
  40868
(1 row)

 setval 
--------
      8
(1 row)

SET
SET
SET
SET
SET
 set_config 
------------
 
(1 row)

SET
SET
SET
SET
COPY 270
 setval 
--------
    270
(1 row)

                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ docker exec -i sg-postgres psql "$NEON_DIRECT_URL" -c "
SELECT round(similarity(name, 'Sergey Lavrov')::numeric, 3) AS score, name
FROM screening_sanctionedentity
WHERE similarity(name, 'Sergey Lavrov') > 0.6
ORDER BY score DESC LIMIT 5;"

 score |     name      
-------+---------------
 0.750 | Sergei Lavrov
(1 row)

                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ DEBUG=False DATABASE_URL="$NEON_DIRECT_URL" uv run manage.py createsuperuser

Username (leave blank to use 'sething2002'): 
Email address: tangpiseth43@gmail.com
Password: 
Password (again): 
Superuser created successfully.
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ uv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"

2=8ser4dg98==kqz$o6*sf-o_@4hzc4*%fonwap*xwud(yq#98
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ git checkout -b hotfix/vercel-drop-functions-config
Switched to a new branch 'hotfix/vercel-drop-functions-config'
                                                                                                                                                                                     
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ git commit -m "fix: drop vercel.json, functions config only applies to api/ dirs"

[hotfix/vercel-drop-functions-config 0ad837e] fix: drop vercel.json, functions config only applies to api/ dirs
 1 file changed, 8 deletions(-)
 delete mode 100644 backend/vercel.json
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ git push
fatal: The current branch hotfix/vercel-drop-functions-config has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin hotfix/vercel-drop-functions-config

                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯     git push --set-upstream origin hotfix/vercel-drop-functions-config
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 327 bytes | 327.00 KiB/s, done.
Total 3 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
remote: 
remote: Create a pull request for 'hotfix/vercel-drop-functions-config' on GitHub by visiting:
remote:      https://github.com/pisethTang/sanctions-graph/pull/new/hotfix/vercel-drop-functions-config
remote: 
To https://github.com/pisethTang/sanctions-graph
 * [new branch]      hotfix/vercel-drop-functions-config -> hotfix/vercel-drop-functions-config
Branch 'hotfix/vercel-drop-functions-config' set up to track remote branch 'hotfix/vercel-drop-functions-config' from 'origin'.
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph/backend 
└─❯ cd ..
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git add .
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git commit -m "A: speech patterns"
[hotfix/vercel-drop-functions-config 90ed449] A: speech patterns
 1 file changed, 3 insertions(+), 2 deletions(-)
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git push
Enumerating objects: 7, done.
Counting objects: 100% (7/7), done.
Delta compression using up to 16 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (4/4), 481 bytes | 481.00 KiB/s, done.
Total 4 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To https://github.com/pisethTang/sanctions-graph
   0ad837e..90ed449  hotfix/vercel-drop-functions-config -> hotfix/vercel-drop-functions-config
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git add .
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git commit -m "fix: add requirements.txt for Vercel's Django install command

The Django preset installs with pip install -r requirements.txt. Without
that file nothing was installed and no function was created, so every
route returned Vercel's 404. Exported from uv.lock so versions match."
[hotfix/vercel-drop-functions-config 6a13e60] fix: add requirements.txt for Vercel's Django install command
 1 file changed, 58 insertions(+)
 create mode 100644 backend/requirements.txt
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git push
Enumerating objects: 6, done.
Counting objects: 100% (6/6), done.
Delta compression using up to 16 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (4/4), 982 bytes | 982.00 KiB/s, done.
Total 4 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To https://github.com/pisethTang/sanctions-graph
   90ed449..6a13e60  hotfix/vercel-drop-functions-config -> hotfix/vercel-drop-functions-config
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ 
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git rm backend/requirements.txt

rm 'backend/requirements.txt'
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git commit -m "D: removed requirements.txt since Vercel detects uv.lock automatically. The build log shows 'Installing required dependencies from uv.lock', so
the file was never read. The actual fix was setting Framework Preset to
Django in project settings.'
∙ "
[hotfix/vercel-drop-functions-config bfb7942] D: removed requirements.txt since Vercel detects uv.lock automatically. The build log shows 'Installing required dependencies from uv.lock', so the file was never read. The actual fix was setting Framework Preset to Django in project settings.'
 1 file changed, 58 deletions(-)
 delete mode 100644 backend/requirements.txt
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git push
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 16 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 443 bytes | 443.00 KiB/s, done.
Total 3 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To https://github.com/pisethTang/sanctions-graph
   6a13e60..bfb7942  hotfix/vercel-drop-functions-config -> hotfix/vercel-drop-functions-config
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ gh pr create --base main --title "fix: deploy Django backend to Vercel" \
  --body "Drops vercel.json (its functions key only matches api/ directories, which broke config validation before the build ran). Framework Preset set to Django in project settings, which is what makes Vercel install from uv.lock and bundle wsgi.py as a function.

Verified on preview: /api/cases/ returns 200 with live Neon data, /admin/ renders with static files."

Creating pull request for hotfix/vercel-drop-functions-config into main in pisethTang/sanctions-graph

https://github.com/pisethTang/sanctions-graph/pull/12
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ gh pr merge --merge

✓ Merged pull request pisethTang/sanctions-graph#12 (fix: deploy Django backend to Vercel)
                                                                                                                            
~/personal-projects/VueDjango/sanctions-graph 
└─❯ git checkout main && git pull

Switched to branch 'main'
Your branch is up to date with 'origin/main'.
remote: Enumerating objects: 1, done.
remote: Counting objects: 100% (1/1), done.
remote: Total 1 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
Unpacking objects: 100% (1/1), 936 bytes | 468.00 KiB/s, done.
From https://github.com/pisethTang/sanctions-graph
   8eeac16..5241bcc  main       -> origin/main
Updating 8eeac16..5241bcc
Fast-forward
 .claude/flagged_speech_patterns.md | 5 +++--
 backend/vercel.json                | 8 --------
 2 files changed, 3 insertions(+), 10 deletions(-)
 delete mode 100644 backend/vercel.json
             


```