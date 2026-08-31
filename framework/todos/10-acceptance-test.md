# TODO 10 — Acceptance Test (the seven steps)

> Status: done — SQLite passes 63/63 (the shipped suite). The 2 Postgres skips are permanent by design, not a gap: §12 decided the package ships SQLite only, with PostgreSQL as an operator-installed production overlay whose role-based append-only enforcement is documented `psql` steps, not shipped migration code — see "Session handoff"
> Blueprint: [§10](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Minimal Working Community"
> Depends on: 02, 03, 04, 05, 06 · Blocks: seed release
> Runs early (as soon as §06 exists) and re-runs after every section.

## Goal
The end-to-end gate. When these seven steps pass on a fresh SQLite install with zero frontend work, the seed model is proven.

## Tasks
- [x] `tests/test_acceptance.py` scripting the seven steps:
  1. `betat init` + declare standard (≥ baseline)
  2. Provenancier enrolls via a protocol-list method
  3. submit a text contribution (content elsewhere, hash provided)
  4. verifier reviews + accepts
  5. valid PROVENANCE_SPEC v0.1 record with `hi_tag:true` + declared standard in store
  6. `/betat/records` returns it; `verify_integrity` passes; no path modifies/deletes it
  7. an independent crawler, given only the host address, discovers + reads it
- [x] Suite is engine-agnostic by construction (only the SQLite-guard-trigger assertion is vendor-gated) — running it against a real PostgreSQL is possible by pointing `DJANGO_SETTINGS_MODULE`/`BETAT_DB` at `settings_production` for manual verification, but §12 decided this is no longer a packaging requirement, so no separate parametrized run ships

## Acceptance criteria
- [x] all seven pass on a fresh SQLite install
- [x] dual-DB ship promise resolved by scope, not by a second passing run: §12 decided the package ships SQLite only; PostgreSQL is an operator-installed overlay (`settings_production.py` + framework-production.md) whose append-only enforcement is documented `psql` role setup, not shipped migration code. The 2 skips in `test_store.py` (SQLite-guard-trigger tests, `connection.vendor != 'sqlite'`) are therefore a **permanent, by-design skip on PostgreSQL**, not a gap waiting on further code.
- [x] zero frontend work required to pass — the suite runs entirely through management commands + the public API
- [ ] the test is the CI gate for a seed release — mechanical CI wiring, now unblocked (no longer waiting on §12) but still a developer action

## Security notes
- Step 6 must assert the absence of any update/delete path, not just that none was called — covered: ORM `.update()`/`.delete()`, instance `.delete()`, API DELETE/PUT/PATCH (401 — `PublicReadOnly` denies at the permission layer before DRF checks for a handler, so an unauthenticated write never reaches one), and raw SQL (SQLite guard trigger)

## Out of scope
- UI polish (§07/§08) — acceptance runs headless via the API

## Session handoff

### §12 resolution (why this moved to `done`)
§12 settled the open item above by scoping decision rather than by building the PostgreSQL role-revocation code this file originally expected: **the package ships SQLite only.** PostgreSQL is a separate, operator-installed production overlay (`betat_community.settings_production`, see [framework-production.md](../../framework-production.md)) — its append-only enforcement is documented `psql` GRANT/REVOKE steps the operator runs themselves, not a Django migration this repo ships or tests automatically. Consequently the two `test_store.py` SQLite-guard-trigger tests are a **permanent** skip on PostgreSQL, not a temporary one — there is no PostgreSQL-specific pytest equivalent to write. Both engines still fully pass everything the shipped suite actually covers (SQLite: all of it; the suite remains engine-agnostic enough to be pointed at a real Postgres manually if anyone wants to verify by hand).

### Path to green — for reference, in case a future Postgres setup hits the same snags
Getting the Postgres leg running surfaced three unrelated environment issues, none of them code bugs:
1. **Docker networking** — this sandbox couldn't reach `localhost:5432` at all until the container's port mapping was fixed (infrastructure, not app config).
2. **Wrong role for testing** — `pytest` was first run against `betatdb`'s `betuser`, which correctly lacks `CREATEDB` (it's the production-shaped role). `betat_testdb`'s `betester` role exists precisely for pytest-django's throwaway `test_*` database. Even then, granting `CREATEDB` had to be done by a superuser (`ALTER ROLE betester CREATEDB;` run *as* `betester` itself silently can't work — a role can't grant itself new attributes).
3. **`betchema` search_path on a brand-new scratch database** — pytest-django's `test_betat_testdb` is created fresh on every run, so it only ever has the default `public` schema; `betat_testdb`'s `OPTIONS: {'options': '-c search_path=betchema'}` had no fallback, so Postgres had "no schema selected" to create tables in. Fixed by dropping the schema override from the test-only block (a scratch database has no reason to use a non-default schema; `betatdb`'s prod-shaped config keeps `betchema`).

Once all three were resolved: `betat_testdb` run → **61 passed, 2 skipped** (the 2 being the SQLite-guard-trigger tests, correctly self-skipping on Postgres).

### Bugs found and fixed while building this section
- `communityauth/api/views.py`'s `EnrollView` checked `method` against the global `PROTOCOL_LIST` but never against `CommunityConfig.auth_methods` — a community that enabled only `cryptographic_signature` would have silently also accepted `community_peer_vouching` enrollments. Fixed (`method_not_enabled` rejection) with a regression test in `test_communityauth.py`. Full rationale in BLUEPRINT §10 Decision Log. §03 stays marked done; this is noted here because the fix landed in a file that section had already shipped.
- The acceptance test itself initially asserted API DELETE/PUT/PATCH on a record would 405. First real run showed 401 instead: `PublicReadOnly` denies non-safe methods at the permission layer, which runs before DRF checks whether a handler exists for the verb — and DRF's `permission_denied()` escalates to `NotAuthenticated` (401) rather than `PermissionDenied` (403)/405 when no credentials were given and `TokenAuthentication` is configured. Not a security gap (the write was always refused) — just a wrong expected status code in the test. Fixed.
- `init.py` was independently rewritten (developer, "Option C") to add operator-declaration/email/preflight checks on top of §02's `CommunityConfig`-writing logic — deliberately anti-automation for a real install (see BLUEPRINT §01/§02 Decision Log). That made `input()` calls unconditional, breaking `test_core.py`/`test_acceptance.py`'s non-interactive `call_command('init', ...)` calls. Fixed in the tests (mock `input()` to answer as a real operator would), not in `init.py` — the unbypassable prompts are intentional.

### Files written this section
- `tests/test_acceptance.py` — the seven-step scenario, new
- `communityauth/api/views.py` — `EnrollView` fix (`method_not_enabled`)
- `tests/test_communityauth.py` — regression test for the fix above
- `pyproject.toml` — added `psycopg[binary]>=3`
- `tests/test_core.py`, `tests/test_acceptance.py` — mock `input()` around `call_command('init', ...)` to match `init.py`'s new operator-declaration/email steps

### Still to do (developer actions)
Mechanical CI wiring for the seed-release gate (run `pytest tests/` on push/PR) — not blocked on anything anymore, just not yet done. Nothing else outstanding.
