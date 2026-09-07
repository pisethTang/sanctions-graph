I asked Claude to generate a logo for this project and it looks pretty good ...


<img src="../logo.svg" alt="SanctionsGraph logo" width="120" />


I took the inspiration from this [repo](https://github.com/rsms/rsm/tree/main). I find his logo comprise of primitives (cicles, lines, flat color) rather than hand-drawn art. 


Came across this [article](https://tom.preston-werner.com/2010/08/23/readme-driven-development.html) by Tom Preston-Werner on readme-driven-development ... quite similar to what I am doing right now.

I decided 

```bash
uv run pytest screening/test_matcher.py -v

=========================================================== test session starts ===========================================================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/.venv/bin/python
cachedir: .pytest_cache
django: version: 6.1.1, settings: sanctionsgraph.settings (from ini)
rootdir: /home/sething2002/personal-projects/VueDjango/sanctions-graph/backend
configfile: pytest.ini
plugins: django-4.14.0
collected 0 items / 1 error                                                                                                               

================================================================= ERRORS ==================================================================
_______________________________________________ ERROR collecting screening/test_matcher.py ________________________________________________
ImportError while importing test module '/home/sething2002/personal-projects/VueDjango/sanctions-graph/backend/screening/test_matcher.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../../../.local/share/uv/python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
screening/test_matcher.py:11: in <module>
    from screening.matcher import ScreenMatcher
E   ModuleNotFoundError: No module named 'screening.matcher'
========================================================= short test summary info =========================================================
ERROR screening/test_matcher.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
============================================================ 1 error in 0.17s =============================================================
```


The next step is for me to 
More TDDs (integration tests) before implementing the api endpoints to:


```bash

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================================================================================ short test summary info ============================================================================================
FAILED screening/test_api.py::TestAgentCreation::test_create_agent - assert 404 == 201
ERROR screening/test_api.py::TestScreening::test_screen_agent_returns_case_and_matches - django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
ERROR screening/test_api.py::TestCaseList::test_list_cases - django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
ERROR screening/test_api.py::TestCaseDetail::test_case_detail_with_matches - django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
ERROR screening/test_api.py::TestNetworkEndpoint::test_network_returns_cytoscape_format - django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
==================================================================================== 1 failed, 1 warning, 4 errors in 0.94s =====================================================================================
                                                                                                

```

# Setup needed after pulling this branch

The matcher branch changes the schema, so `git pull` on its own is not enough. Two things are
new: `Agent.addresses` (a JSON list of dicts like `[{"full_text": "...", "country_code": "..."}]`)
and the `pg_trgm` extension, which is what provides the `similarity()` function that the fuzzy
name and address steps call.

Normally this is just:

```bash
cd backend
uv run manage.py migrate
```

Migration `0003_agent_addresses_trigram` runs `TrigramExtension()` before adding the field, so
`CREATE EXTENSION pg_trgm` happens automatically. That only works if the database role is allowed
to create extensions. `sguser` is the superuser in my local container so it is fine, but a managed
Postgres (Railway, RDS) will often refuse it.

If migrate fails with a permission error on the extension, create it by hand first and then run
migrate again. Django will see it already exists and skip it:

```bash
uv run manage.py dbshell
```

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\dx
\q
```

`\dx` lists installed extensions, want to see `pg_trgm` in there:

```
  Name   | Version |   Schema   |                     Description
---------+---------+------------+-----------------------------------------------------
 pg_trgm | 1.6     | public     | text similarity measurement and index searching ...
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
```

Same thing without opening a shell, since dbshell here means going through the container anyway:

```bash
docker exec sg-postgres psql -U sguser -d sanctionsgraph -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

And remember postgres has to be up before any of this, otherwise it is yesterday's connection
refused all over again:

```bash
docker start sg-postgres
```
