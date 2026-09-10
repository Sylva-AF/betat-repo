# TODO 12 — Packaging & Production Guide

> Status: in progress — packaging decision made and implemented (SQLite-default ship, `BETAT_DB` for PostgreSQL, no code changes either way); production guide written; `betat init` now writes `manage.py`; wheel/sdist built and `twine check` passed 2026-09-08; fresh-venv install check passed end-to-end 2026-09-09 after three real bugs found and fixed (migrate-ordering, auth-methods prompt UX, missing templates/static in the wheel — see updates below). A fourth bug (peer-vouch bootstrap catch-22) found and fixed 2026-09-09, code-complete but explicitly deferred (not migrated/tested/rebuilt) — **however, as of 2026-09-10 the migration and code landed on `main` anyway** (commit `7e982d9`), unintentionally: it had been `git add`-ed in a prior session and sat staged until an unrelated commit swept it in. **The verification pipeline still has NOT run against it** — no `pytest` run against the actual migration, no wheel rebuild, no fresh-venv check. **Start here next session: "Update 2026-09-10 — session deferred" (near the bottom of this file) has the consolidated script** — steps 1-2 (migrate/test) are now redundant with what's on `main` but safe to re-run for confirmation; steps 3-6 (rebuild, fresh-venv verify) are still the real gap. Also see the correction note right below this line.
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
1. **Run the dual-DB ship gate** (DISTRIBUTION.md pre-release checklist, now a real requirement again): point `BETAT_DB` at a live PostgreSQL instance and re-run `pytest tests/` — everything should pass except the two permanently-skipped SQLite-guard-trigger tests. **Not attempted yet** (see Update 2026-09-08 below — this session did the build/twine steps of item 2, not this one).
2. **Build the package and verify a clean install** (see DISTRIBUTION.md "How to build and publish" for the full sequence — that file's exact invocation is authoritative over this list, see the update below):
   ```bash
   python -m build ./framework                                  # from the repo root, venv active — DONE 2026-09-08
   twine check framework/dist/*                                 # DONE 2026-09-08, both PASSED
   python3.11 -m venv /tmp/betat-test && source /tmp/betat-test/bin/activate
   pip install framework/dist/betat_community-0.1.0-py3-none-any.whl   # fresh venv, not -e — NOT YET RUN
   betat --help                                                # should work with zero config
   betat init                                                  # should write manage.py
   python manage.py migrate                                   # SQLite, zero config
   ```
3. **Dry-run `framework-production.md`** once against a real PostgreSQL instance (local Docker Postgres is fine) — confirm the role setup and the REVOKE actually blocks a raw UPDATE/DELETE as the app role. This is the one part of this section not yet exercised for real.
4. `git rm betat_community/settings_production.py` — retired, no longer referenced anywhere.
5. Once 1–4 are clean, flip this file's status to `done`, update `TODO.md`'s row 12, and proceed to the actual PyPI publish per DISTRIBUTION.md (register the `betat-community` name first if not already done).
6. Optional/unblocked-not-required: wire `pytest tests/` as a CI gate (TODO 10's last open checkbox).
7. ~~Worth a follow-up: add a direct unit test for `_write_manage_py()`'s actual write path~~ — **done**: `tests/test_core.py::test_init_writes_manage_py` and `::test_init_does_not_overwrite_existing_manage_py` now cover both the write and no-op branches via `tmp_path`/`monkeypatch.chdir`. Not yet run (developer runs pytest) — expected to pass alongside the existing 95.

### Update 2026-09-08 — first wheel/sdist build attempt

Ran the build for the first time. One correction found along the way:
this file's item 2 above originally said `cd framework; python -m build`
— the actual authoritative command, per DISTRIBUTION.md's "How to build
and publish" (which this file's own header names as authoritative for
this section), is to stay at the **repo root** with the venv active and
pass the framework directory as an argument: `python -m build
./framework`. "Repo root" and "the docker workspace" are the same
location here — root CLAUDE.md: the build runs inside the
`betat-sandbox` container with the repo bind-mounted at `/workspace`.

Steps completed, in order:
1. `pip install build twine` (one-time prerequisite — `build` wasn't
   installed yet, caused a `No module named build` error first attempt).
2. `python -m build ./framework` — **succeeded**:
   `framework/dist/betat_community-0.1.0.tar.gz` and
   `framework/dist/betat_community-0.1.0-py3-none-any.whl` both built.
3. `twine check framework/dist/*` — **PASSED** for both files.

**Not yet done — pick up here:** the fresh-venv install check (item 2's
last four lines above) was handed off as the next command but its
outcome wasn't reported before the session ended. Run it, then continue
down this file's numbered list from item 1 (dual-DB gate, not yet
attempted this session) and item 3 onward.

### Update 2026-09-09 — fresh-venv install check found and fixed a real blocking bug

Ran the fresh-venv install check (item 2 of "Still to do") for the first
time, on a real Rocky Linux 9 host. Install itself succeeded cleanly
(`pip install` from the built wheel, `betat --help` worked). Along the way,
one environment-side finding and one confirmed code bug:

- **Environment finding, not a framework bug:** the test host's Python 3.11
  had been built from source without `sqlite-devel` present, so `_sqlite3`
  was silently missing. Rebuilt Python after installing `sqlite-devel` and
  re-running `./configure && make && sudo make altinstall` — not a Betat
  issue, but it exposed the bug below.
- **Confirmed bug, now fixed:** `betat init` unconditionally crashed with
  `OperationalError: no such table: core_communityconfig` on every fresh
  install, every time, regardless of host. Root cause: `init.py`'s
  `handle()` called `CommunityConfig.objects.exists()` before any
  migration had ever run — and per `cli.py`'s own Decision Log, `betat`
  deliberately does not wrap `migrate` (`manage.py` doesn't even exist
  until `init` writes it near the end of `handle()`), so there was no
  order in which an operator could run migrations first. This wasn't
  test-covered because pytest-django's `django_db` fixture always applies
  migrations before any test body runs — no existing test exercised a
  true pre-migration state.
  **Fix:** `init.py`'s `handle()` now calls
  `call_command('migrate', verbosity=0, interactive=False)` as its first
  step, before the `CommunityConfig.objects.exists()` guard. Idempotent —
  the documented `python manage.py migrate` in step 6 of "What the
  operator experiences" becomes a harmless no-op re-run.
- **Related finding, also fixed:** the SQLite/Python-version preflight
  check (`_preflight_issues()`) lived inside `init.py`'s `handle()`, but
  was unreachable dead code for the SQLite case specifically —
  `django.setup()` (app loading, triggered before any command's
  `handle()` runs) itself crashes with a raw traceback importing the
  DB backend the moment `django.contrib.auth.models.AbstractBaseUser` is
  defined, which is exactly what produced the confusing traceback earlier
  in this session before the real cause was found. Moved
  `_preflight_issues()` from `init.py` to `cli.py`, called in `main()`
  before `execute_from_command_line()` — now runs before Django loads at
  all, for every `betat <command>`, not just `init`.

Files changed: `betat_community/core/management/commands/init.py`
(removed `_preflight_issues()` and its module-level `import sys`, added
`call_command('migrate', ...)` as the new first step of `handle()`),
`betat_community/cli.py` (added `_preflight_issues()`, called from
`main()` before Django import). No test currently asserts on this
ordering directly (see above — pytest-django's fixture makes a genuine
pre-migration regression test impractical to construct), but the
existing `init`-command test suite (`tests/test_core.py`,
`tests/test_acceptance.py`) exercises the changed code path on every run
and remains green.

**Confirmed:** `pytest tests/` — 133/133 passed with the migrate fix in place.

### Update 2026-09-09 — two more bugs found continuing the fresh-venv check

Resumed the fresh-venv check with the rebuilt wheel. `betat init` got past
the `CommunityConfig` guard this time, but surfaced two more real bugs —
both fixed:

- **`init.py` auth_methods prompt UX bug.** The interactive "Authentication
  method(s), comma-separated" prompt never showed the allowed values and
  never validated before `config.save()` — unlike `content_type`, which
  uses `_prompt_choice()` to loop-validate in place. A human-readable guess
  ("Peer Vouch" instead of the actual key `community_peer_vouching`) sailed
  through every other prompt (community id with DNS check, name, domain,
  content type, store URI) only to blow up at the very last step with a
  raw `CommandError`, discarding every answer already given — no partial
  save, full restart required. **Fix:** added `_prompt_auth_methods()`
  (mirrors `_prompt_choice()`'s loop-until-valid pattern), validated
  against `AUTH_METHOD_KEYS = list(PROTOCOL_LIST)` imported from
  `betat_community.communityauth.floor`. Confirmed via a verification
  agent that no existing test exercises this interactive path (all
  `test_core.py`/`test_acceptance.py` calls pass `auth_methods` as a
  kwarg, bypassing the prompt) — so this fix has no regression risk but
  also no direct test coverage yet; worth a follow-up unit test.
- **Packaging bug — the wheel shipped with no templates or static files.**
  `betat start` (`runserver`) booted fine, but every page 500'd:
  `TemplateDoesNotExist: bundledui/installer/install.html`. Root cause:
  `pyproject.toml` had no `package-data`/`MANIFEST.in` config at all, so
  `python -m build` only ever included `.py` files — every wheel built
  to date (including the 2026-09-08 build) silently shipped without
  `bundledui`'s 24 HTML templates or `betat.css`. This is the single
  most serious finding of this section: the CLI worked, `init` worked,
  but the actual web UI was completely broken in every packaged install,
  editable installs (`pip install -e`) masked it since they symlink to
  the source tree. **Fix:** added
  `[tool.setuptools.package-data]` / `"*" = ["templates/**/*", "static/**/*"]`
  to `pyproject.toml`. Also fixed a stale comment above `dependencies`
  that still described the old, reversed "strip settings.py before
  release" approach — corrected to match DISTRIBUTION.md's actual
  current design (BETAT_DB support ships permanently).

**Confirmed 2026-09-09 — fresh-venv install check now passes end-to-end.**
Rebuilt wheel, fresh venv, fresh project dir: `betat init` completed
fully (auth-methods prompt correctly rejected an invalid entry and
re-prompted without losing prior answers, then accepted
`community_peer_vouching`), `createsuperuser` worked, `betat start`
served `GET /` → 200, `GET /static/bundledui/styles/betat.css` → 200
(confirms the packaging fix — templates and static files are now
actually in the wheel), and manual clicking through `/community/records`,
`/community/login`, `/community/enroll`, `/community/queue` all
returned 200. **TODO 12's "clean install from built artifact works"
acceptance criterion is now met.**

One thing flagged for a follow-up look, not confirmed as a bug: a
`Unauthorized: /betat/login` line appeared in the server log between the
`/community/login` GET and POST — possibly an expected client-side
auth-status check against the public API namespace (`/betat/`, distinct
from the bundledui page at `/community/login`), possibly not. Not
investigated further this session since the operator-facing pages all
rendered correctly.

**Still not done:** the dual-DB Postgres ship gate (`BETAT_DB` against a
live PostgreSQL instance, re-run `pytest tests/`), the production-guide
dry run against real PostgreSQL, `git rm betat_community/settings_production.py`.
These block the actual `done` status and PyPI publish — see the
numbered "Still to do" list above, items 1, 3, 4 remain open.

### Update 2026-09-09 — PICK UP HERE next session: peer-vouch bootstrap catch-22

While manually testing the founding-phase install just above (`bantu.org`
test community), hit a **product-level dead end**, not a crash: the
operator had enabled only `community_peer_vouching` during `betat init`.
The first-ever provenancier's enrollment requires 2 existing enrolled
members to vouch — but 0 exist on a fresh install, so the request could
never complete. `BLUEPRINT.md`'s prior §10 decision (2026-08) answered a
version of this by routing first members through `CryptoKeyAuth` instead
— but that only helps an operator who *also* enables that method; nothing
warns an operator who picks peer-vouch alone, which is exactly what
happened here.

**Fixed with a founding phase**, not a docs warning or an `init`-time
guard (both considered, both rejected — full rationale in the new
BLUEPRINT §03 Decision Log entry dated 2026-09-09, which explicitly
supersedes §10): `PeerVouchRequest` gains a `founding` field.
`PeerVouchAuth.enroll()` now checks `Provenancier.objects.count() < 2` at
request creation; if true, it skips the vouch-threshold path entirely and
returns a new `pending_admin` outcome instead, promoted via a new Django
admin action (`communityauth/admin.py`'s `approve_founding_requests`) —
the system self-bootstraps automatically, no operator configuration
needed either way. Full design detail: `todos/03-authentication.md`'s
2026-09-09 addendum (this is really a §03 change, logged there; noted
here because this file is what gets read first next time).

**Everything is code-complete — six files changed, tests fixed/added —
but NONE OF IT HAS BEEN RUN YET.** Do these in exact order next session:

```bash
# 1. Generate and apply the migration for the new `founding` field —
#    without this, every new test below fails with "no such column".
cd /workspace/framework
python manage.py makemigrations communityauth
python manage.py migrate

# 2. Full suite — 133 previous + 5 new tests this fix added = 138 expected
pytest tests/

# 3. Only once #2 is green: rebuild the wheel (it does NOT yet contain
#    this fix — the last build was before this change)
cd /workspace
rm -rf framework/dist
python -m build ./framework
twine check framework/dist/*

# 4. Fresh venv, fresh project dir (don't reuse /tmp/betat-test-project —
#    its DB predates the `founding` column entirely)
rm -rf /tmp/betat-test
python3.11 -m venv /tmp/betat-test
source /tmp/betat-test/bin/activate
pip install framework/dist/betat_community-0.1.0-py3-none-any.whl
rm -rf /tmp/betat-test-project && mkdir /tmp/betat-test-project && cd /tmp/betat-test-project
betat init          # enable community_peer_vouching again, on purpose —
                     # this time the first enrollment should show
                     # "Awaiting administrator approval", not an
                     # impossible vouch count
python manage.py createsuperuser
betat start
```

Then: enroll a first test provenancier via peer-vouch, confirm the
pending page shows the founding message (not vouch counts), approve it
via `/admin/` → `PeerVouchRequest` → select it → "Approve selected
founding-member requests" action → confirm a `Provenancier` + token now
exist and the request row is gone.

**Files changed this fix:** `BLUEPRINT.md` (§03 Decision Log),
`betat_community/communityauth/models.py` (`founding` field),
`betat_community/communityauth/plugins/peer_vouch.py` (`enroll()` +
`_promote`→`promote` rename), `betat_community/communityauth/admin.py`
(new `approve_founding_requests` action), `betat_community/bundledui/
views.py` (`_render_peer_vouch_pending` founding branch),
`betat_community/bundledui/templates/bundledui/community/
enroll_pending.html` (founding branch), `tests/test_communityauth.py`
(2 tests fixed, 4 new), `tests/test_bundledui.py` (2 tests fixed, 1 new),
`todos/03-authentication.md` (addendum).

**Not yet re-verified after this fix:** whether the un-migrated
`bantu.org` test community from earlier in this session is worth keeping
around — recommend abandoning it (fresh `/tmp/betat-test-project` per the
commands above) rather than trying to migrate a pre-`founding`-column
SQLite file in place.

### Update 2026-09-10 — session deferred, then corrected: the deferred work landed on `main` anyway

Intent this session was to defer all of §12 to guarantee a clean,
fully-verified v0.1 before the PyPI name is claimed (registering
`betat-community` and publishing is effectively a one-way door: the name is
hard to reclaim/change once operators depend on it). Re-verified the code
state this session (`models.py`'s `founding` field, `peer_vouch.py`'s
`enroll()`/`promote()`, `admin.py`'s `approve_founding_requests` all present
as described) and confirmed at that point nothing had been migrated,
tested, or rebuilt.

**Correction, later the same session:** an unrelated commit (the enroll/
submit help-icon UI fix, see below) ended up including the founding-phase
migration and code anyway. Cause: `git commit -m "..."` with no pathspec
commits everything currently staged, not just what was just `git add`-ed —
and the founding-phase files had apparently been staged since a prior
session and never committed (this is the exact "open question" an earlier
update in this file flagged: *"whether any of this was actually committed
— run git status/git log first"* — it wasn't, this time). Net result:
`communityauth/migrations/0003_peervouchrequest_founding.py` and all the
founding-phase code are now on `main`, pushed, as of commit `7e982d9`
(2026-09-10) — **without ever having been run through `pytest`, rebuilt
into a wheel, or fresh-venv verified.** A second stray file
(`vouching-review/vouch-snippet.md`, unrelated content that doesn't match
this codebase — wrong paths/field names/template names) rode along in the
same commit and is being removed in a follow-up.

**Practical effect on the plan below:** the "PICK UP HERE" script's steps
1-2 (`makemigrations`/`migrate`, `pytest tests/`) are now about *confirming*
what's already on `main` rather than applying new changes — run them
anyway, since none of this has actually been executed yet, just committed.
Steps 3-6 (retire `settings_production.py`, rebuild, fresh-venv check) are
still the real open gap and haven't changed. **Lesson for future sessions:
run `git status` before any `git add`/`git commit` sequence, not after —
don't assume the index only contains what you just staged.**

**Start next session with this consolidated script** (combines the
"PICK UP HERE" migration/test/rebuild steps with DISTRIBUTION.md's
pre-release checklist — stops before the actual `twine upload` so results
can be reviewed first):

```bash
#!/usr/bin/env bash
set -e

# 1. Apply the founding-phase migration
cd /workspace/framework
python manage.py makemigrations communityauth
python manage.py migrate

# 2. Full test suite — expect 138 (133 previous + 5 new)
pytest tests/

# 3. Retire the superseded settings module (still present as a stub —
#    confirmed not yet removed as of 2026-09-10)
cd /workspace
git rm framework/betat_community/settings_production.py

# 4. Sanity check
cd /workspace/framework
python manage.py check

# 5. Rebuild the wheel/sdist — the last build predates the founding-phase fix
cd /workspace
rm -rf framework/dist
python -m build ./framework
twine check framework/dist/*

# 6. Fresh venv, fresh project — confirm the founding-phase fix end-to-end
rm -rf /tmp/betat-test
python3.11 -m venv /tmp/betat-test
source /tmp/betat-test/bin/activate
pip install framework/dist/betat_community-0.1.0-py3-none-any.whl
rm -rf /tmp/betat-test-project && mkdir /tmp/betat-test-project && cd /tmp/betat-test-project
betat init          # enable community_peer_vouching again — first enrollment
                     # should show "Awaiting administrator approval", not an
                     # impossible vouch count
python manage.py createsuperuser
# betat start; enroll a first test provenancier; approve via /admin/ ->
# PeerVouchRequest -> "Approve selected founding-member requests"; confirm
# a Provenancier + token now exist and the request row is gone.
```

**Still open after that script (developer actions, unscripted):**
1. The dual-DB ship gate — point `BETAT_DB` at a live PostgreSQL (local
   Docker is fine), rerun `pytest tests/`; everything should pass except
   the two permanently-skipped SQLite-guard-trigger tests. Not attempted
   yet at all this project.
2. Dry-run `framework-production.md` against that same real PostgreSQL —
   confirm the role setup and the REVOKE actually blocks a raw UPDATE/DELETE
   as the app role. Never exercised for real.
3. Only once 1–2 above are clean: `twine upload framework/dist/*`
   (`__token__` + API token — register the `betat-community` name on
   pypi.org first if not already done), then attach the same `dist/*`
   files to a `v0.1.0` GitHub Release per DISTRIBUTION.md.
4. Flip this file's status to `done`, update `TODO.md` row 12.

### Also this session (unrelated to §12) — enroll/submit form help icons, committed

Not part of packaging — this session's other thread, flagged here for the
same reason as the nav-polish note below (this file gets read first next
time; `TODO.md` still shows §12 `in progress`).

Field labels and inline guide/hint text on the enroll and submit forms
previously rendered in the same muted color and blended together, and the
pages read as wall-of-text. Fixed: `.bt-label-field` is now bold/ink-colored
(was the same muted gray as body/hint text); secondary explanations moved
behind a small ⓘ icon next to the label — click to open, click again to
close (pure-CSS "checkbox hack": a visually-hidden `<input type="checkbox">`
+ a `<label>` pointing at it + a `:checked ~` sibling selector — no JS,
consistent with the toast messages' no-JS convention below). Explanation
text was also rewritten in plainer language (e.g. content_hash's tooltip
now explains what SHA-256 is and gives a runnable command), and coverage
was widened beyond the fields that already had inline hints — `method` and
`identity` on enroll, `language` on submit also got icons.

Left inline, deliberately not moved behind an icon: the passphrase
paragraph on enroll.html (contains a live "log back in" link — a link
inside a tooltip that closes when you move toward it is broken UX) and the
declaration checkbox text on submit.html (the actual legal declaration
being agreed to, not decorative guidance).

Files changed: `bundledui/static/bundledui/styles/betat.css` (`.bt-label-field`
weight/color, new `.bt-help`/`.bt-help-toggle`/`.bt-help-icon`/`.bt-help-text`
rules), `bundledui/templates/bundledui/community/enroll.html`,
`bundledui/templates/bundledui/community/submit.html`. No test changes — CSS/
template-only, no behavior for pytest to assert on. **Committed and pushed
this session** (commit `7e982d9`) — but the commit was NOT scoped to just
these 3 files; see the correction note above ("session deferred, then
corrected") for what else rode along and why.

### Also this session (unrelated to §12) — peer-vouch pending-state UI + nav polish

Not part of packaging — flagging here only because it's this session's
other thread and this file is the one most likely to be read first next
time (`TODO.md` still shows this section `in progress`).

- Built the `enroll_view` persistent pending-state page for
  `community_peer_vouching` applicants (new `enroll_pending.html`,
  `betat.css` additions, one new BLUEPRINT §03 Decision Log entry dated
  2026-09 with the full design rationale and a documented honest gap —
  see that entry for detail, not repeated here) plus 3 new tests in
  `tests/test_bundledui.py`.
- Follow-on nav/UX polish after that, all template/CSS-only: the login/
  logout CTA moved out of the section-nav row into its own bordered pill
  at the far right (`base.html`, `.bt-nav-cta` in `betat.css`); hover
  tooltips (`title` attrs) added to all five nav links; "Submit" renamed
  to "Submit Content" to match that page's own `bt-label`; flash
  messages restyled as a pure-CSS auto-fading toast (`.bt-toast-wrap`/
  `.bt-toast`, fixed position below the nav, `@keyframes` fade in/hold/
  fade out, paused on hover, no JS); base `.bt-banner` background
  changed from `--bt-warm` (identical to the page background) to
  `--bt-paper`, since untagged/info-tagged messages were rendering
  invisible against the page.
- Test status: 133/133 passing as of the last confirmed `pytest tests/`
  run, which was **before** the nav-polish round (CTA move, tooltips,
  Submit Content rename, toast, banner background). Those later edits
  don't touch anything the existing suite asserts on (checked by hand),
  but were never re-verified with an actual pytest run before the
  session ended — run `pytest tests/` once as a sanity check if that
  hasn't happened yet.
- **Open question, check first:** whether any of this was actually
  committed/pushed. The developer asked "Ok to deploy?", got a go-ahead
  plus the pytest-once-more suggestion, then the conversation moved
  straight into the wheel-build thread above without confirming a git
  commit happened. Run `git status`/`git log` first thing to find out
  before assuming it's landed.
- Files touched: `bundledui/views.py`, `bundledui/templates/bundledui/
  community/enroll_pending.html` (new), `bundledui/templates/bundledui/
  community/base.html`, `bundledui/static/bundledui/styles/betat.css`,
  `BLUEPRINT.md` (§03 Decision Log), `tests/test_bundledui.py`.
