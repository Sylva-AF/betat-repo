# TODO 01 — Project Scaffold & CLI

> Status: done
> Blueprint: [§1](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "What an Operator Gets"
> Depends on: nothing (first section) · Blocks: all

## Goal
The installable skeleton: `pip install -e "./framework[dev]"` works, the `betat` CLI exists as a thin dispatcher, Django boots with the six apps registered and SQLite as default. When done, every later section has a place to live and a way to run.

## Tasks
- [x] `framework/pyproject.toml`: name `betat-community`, `requires-python = ">=3.11"`, deps `django>=5,<6`, `djangorestframework`; `[dev]` extra: `pytest`, `pytest-django`
- [x] Console entry point: `betat = "betat_community.cli:main"`
- [x] `betat_community/` project: `settings.py` (INSTALLED_APPS incl. DRF + the six apps as stubs), `urls.py`, `wsgi.py`, `asgi.py`
- [x] `settings.py` DB: SQLite at env `BETAT_DB` or `./betat.sqlite3`; `BETAT_SECRET_KEY` env override
- [x] `cli.py`: parse first token (`init`/`runserver`/`check`/`announce`/`export`) → delegate to the matching management command
- [x] `manage.py` at `framework/` level
- [x] Six empty app packages with `apps.py` only: core, store, communityauth, workflow, federation, bundledui
- [x] `pytest.ini` / pyproject `[tool.pytest.ini_options]` with `DJANGO_SETTINGS_MODULE`

## Acceptance criteria
- [x] `pip install -e "./framework[dev]"` succeeds on Python 3.11
- [x] `betat --help` lists all five commands
- [x] `python manage.py check` passes
- [x] `pytest` runs green with zero tests
- [x] each command is runnable both as `betat <cmd>` and `manage.py <cmd>` (init/announce/export are stubs — real logic is §02/§09's job)

## Security notes
- `BETAT_SECRET_KEY` must have no committed default usable in production; generate-or-fail on missing in non-debug
- SQLite default path stays inside the project and is gitignored

## Out of scope
- Any model or endpoint (later sections) — this is skeleton only
- Auth logic (§03), store logic (§05)
