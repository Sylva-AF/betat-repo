# TODO 12 — Packaging & Production Guide

> Status: in progress — packaging decision made and implemented (SQLite-default ship, `BETAT_DB` for PostgreSQL, no code changes either way); production guide written; `betat init` now writes `manage.py`; build/install verification and a live-Postgres dry run are developer actions (see "Still to do")
> Blueprint: [§12](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Design Goal 4", "storage engines"
> Depends on: 01-10 · Blocks: seed release
> Read alongside: [DISTRIBUTION.md](../DISTRIBUTION.md) — the authoritative build/publish guide for this section

## Key decisions this section made
1. **`settings.py` reads `BETAT_DB` unconditionally, for both engines, permanently.** No `BETAT_DB` set means SQLite (zero configuration, fine for evaluation). Set to a PostgreSQL URL and the *same installed package* connects to PostgreSQL — no code changes, no separate settings module, nothing stripped before a release build. (Two earlier approaches this session — a `settings_production.py` overlay, and literally stripping the Postgres path from `settings.py` before packaging — were both tried and corrected: neither works for a real `pip install`ed package, since operators can't realistically hand-edit a file inside `site-packages/`. Full history: BLUEPRINT §12 Decision Log, and the "CORRECTED" entries in it.)
2. **PostgreSQL's role-based append-only enforcement is documented `psql`, not shipped migration code.** PostgreSQL table ownership can't be stripped by REVOKE, so genuine enforcement needs two roles (a migrator/owner role that runs `migrate`, and a restricted app role the server actually connects as) — automating and testing that split in this repo would need a live two-role Postgres in CI this project doesn't have. [framework-production.md](../../framework-production.md) documents the exact SQL instead. This resolves TODO 10's Postgres-testing gap by scope: its two SQLite-guard-trigger tests are a **permanent** skip on PostgreSQL, not a temporary one.
3. **`betat init` writes a standard `manage.py`.** The package ships only the importable `betat_community` package (no top-level script gets bundled) — so a bare `pip install betat-community` gave `betat init/runserver/check/announce/export` but no way to run `migrate` or `createsuperuser`, both essential. `betat init` now writes the standard `django-admin startproject`-template `manage.py` to the working directory (idempotent — no-ops if one already exists), right after writing the `.env` accountability record. From there it's plain Django.

## Tasks
- [x] Finalize `pyproject.toml` — added PyPI metadata (`readme`, `keywords`, `classifiers`, `[project.urls]`) per DISTRIBUTION.md; `psycopg[binary]`/`dj-database-url` stay plain `dependencies` (not an extra — `settings.py` imports `dj_database_url` unconditionally, so it must always be present)
- [ ] Build + verify a wheel/sdist, and that `pip install` from the built artifact works clean (not just `-e`) — **developer action**, see "Still to do" and DISTRIBUTION.md
- [x] "Recommended production stack" guide: PostgreSQL install, config, and role setup — app role INSERT/SELECT only, UPDATE/DELETE revoked ([framework-production.md](../../framework-production.md))
- [x] SQLite → PostgreSQL migration route, documented (`dumpdata`/`loaddata`, framework-production.md § "Moving existing data") — not yet dry-run against a live Postgres this session, see "Still to do"
- [x] Document Python 3.11 floor, tested through 3.12+ (unchanged from §1; noted again in the production guide)
- [x] `betat init` writes `manage.py` — closes the gap where a pip-only install had no way to run `migrate`/`createsuperuser`

## Acceptance criteria
- [ ] clean install from built artifact works — **developer action**
- [x] dual-DB ship promise: real, not scoped away — `settings.py` supports both engines via `BETAT_DB`; the dual-DB ship gate (point `BETAT_DB` at a live Postgres, re-run `pytest tests/`) is a real DISTRIBUTION.md pre-release checklist item — **developer action to actually run**, see "Still to do"
- [x] the ONLY production step documented for end users is: set `BETAT_DB` and deploy (no code changes) — framework-production.md
- [ ] production guide runs end-to-end — written, not yet dry-run against a real PostgreSQL instance; **developer action**
- [ ] on PostgreSQL, raw UPDATE/DELETE by the app role fails at the DB-permission level — documented as operator-run `psql` (framework-production.md §3), not automatically tested by this repo; verify once when first dry-running the guide

## Security notes
- The production guide's role revocation is the REAL append-only boundary — emphasized in framework-production.md over the SQLite triggers, and the guide never claims SQLite matches it
- Secret-key and DB-credential handling documented via env vars only (`BETAT_DB`, `BETAT_SECRET_KEY`) — no credentials committed anywhere in this section's changes (the old dev-only inline-credential Postgres blocks in settings.py were deleted, not migrated forward)
- `manage.py`'s content is Django's own unmodified startproject template — no betat-specific code added to it, nothing to audit beyond what every Django project already has

## Out of scope
- New features — this section hardens and ships what §1-§10 built

## Session handoff

### Files written/changed this section
- `betat_community/settings.py` — removed the two commented-out dev-only Postgres blocks (inline credentials); `DATABASES` now built via `dj_database_url.config(env='BETAT_DB', default=<sqlite path>)` — same env var as before, now URL-capable for both engines, permanently (not stripped before a release build)
- `betat_community/settings_production.py` — **retired**, tried and corrected mid-session (see BLUEPRINT §12 Decision Log). Currently neutered to a one-line stub with a removal note — **`git rm` this file**
- `betat_community/core/management/commands/init.py` — `handle()` now calls `_write_manage_py()` right after `_write_env_record()`; writes the standard Django `manage.py` (verbatim `django-admin startproject` template content) to the working directory if one doesn't already exist
- `pyproject.toml` — added PyPI metadata block (readme/keywords/classifiers/urls) per DISTRIBUTION.md; `psycopg[binary]`/`dj-database-url` confirmed as plain dependencies, not an extra
- `DISTRIBUTION.md` — corrected in place (not append-only there, unlike BLUEPRINT's Decision Log): "What ships" and the pre-release checklist no longer say to strip `settings.py`'s Postgres path before building
- `framework-production.md` — new root-level doc page (repo root, not `framework/` — Jekyll convention per TODO 11), `parent: For Builders`, `nav_order: 9`. Two-role setup with literal SQL, migrate-as-migrator/run-as-app-role split (via plain `python manage.py migrate`, since `betat init` now provides one), SQLite→Postgres data migration, Python version note.
- `framework-cli.md`, `framework-reference.md` — updated the database-configuration section (restored `BETAT_DB` as directly Postgres-capable, no separate module) and doc index to link the new guide; noted `betat init` now writes `manage.py`
- `tests/test_acceptance.py` — updated the module docstring to describe the actual dual-DB story (real ship gate via `BETAT_DB`, permanent skip only on the two guard-trigger tests)
- `todos/10-acceptance-test.md`, `TODO.md` — TODO 10 moved to `done`

### Why two DB roles, and why enforcement isn't automated in CI
PostgreSQL table ownership can't be stripped by REVOKE — an owner always retains UPDATE/DELETE regardless of grants. So genuine enforcement needs a migrator/owner role (runs `migrate`) distinct from the app's runtime role (INSERT/SELECT only). Automating and testing that split inside this repo would mean either shipping a migration that REVOKEs from a role named via a new env var with no live two-role Postgres in CI to verify it against, or standing up real Postgres CI infrastructure. `framework-production.md` §1 and §3 documents the exact `psql` commands instead — honest, and verifiable by any operator who runs them.

### Still to do (developer actions)
1. **Run the dual-DB ship gate** (DISTRIBUTION.md pre-release checklist, now a real requirement again): point `BETAT_DB` at a live PostgreSQL instance and re-run `pytest tests/` — everything should pass except the two permanently-skipped SQLite-guard-trigger tests.
2. **Build the package and verify a clean install** (see DISTRIBUTION.md "How to build and publish" for the full sequence):
   ```bash
   cd framework
   python -m build
   twine check dist/*
   pip install dist/betat_community-0.1.0-py3-none-any.whl   # in a fresh venv, not -e
   betat --help                                                # should work with zero config
   betat init                                                  # should write manage.py
   python manage.py migrate                                   # SQLite, zero config
   ```
3. **Dry-run `framework-production.md`** once against a real PostgreSQL instance (local Docker Postgres is fine) — confirm the role setup and the REVOKE actually blocks a raw UPDATE/DELETE as the app role. This is the one part of this section not yet exercised for real.
4. `git rm betat_community/settings_production.py` — retired, no longer referenced anywhere.
5. Once 1–4 are clean, flip this file's status to `done`, update `TODO.md`'s row 12, and proceed to the actual PyPI publish per DISTRIBUTION.md (register the `betat-community` name first if not already done).
6. Optional/unblocked-not-required: wire `pytest tests/` as a CI gate (TODO 10's last open checkbox).
7. ~~Worth a follow-up: add a direct unit test for `_write_manage_py()`'s actual write path~~ — **done**: `tests/test_core.py::test_init_writes_manage_py` and `::test_init_does_not_overwrite_existing_manage_py` now cover both the write and no-op branches via `tmp_path`/`monkeypatch.chdir`. Not yet run (developer runs pytest) — expected to pass alongside the existing 95.
