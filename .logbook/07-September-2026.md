I asked Claude to generate a logo for this project and it looks pretty good ...


<img src="../logo.svg" alt="SanctionsGraph logo" width="120" />


I took the inspiration from this [repo](https://github.com/rsms/rsm/tree/main). I find his logo comprise of primitives (cicles, lines, flat color) rather than hand-drawn art. 


Came across this [article](https://tom.preston-werner.com/2010/08/23/readme-driven-development.html) by Tom Preston-Werner on readme-driven-development ... quite similar to what I am doing right now.



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