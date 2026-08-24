# TODO 10 — Acceptance Test (the seven steps)

> Status: in progress — both engines pass everything currently buildable (SQLite 63/63; Postgres 61/63 + 2 expected skips); the only remaining gap is §12's PostgreSQL role-revocation enforcement (see "Session handoff")
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
- [ ] Parametrize the suite (or provide a second run) so it executes under both BETAT_DB settings: SQLite and PostgreSQL — **partially unblocked**, see handoff

## Acceptance criteria
- [x] all seven pass on a fresh SQLite install
- [x] all seven ALSO pass against PostgreSQL, for everything currently buildable — `betat_testdb` run: 61 passed, 2 skipped. The 2 skips are `test_store.py`'s SQLite-guard-trigger tests, correctly self-skipping (`connection.vendor != 'sqlite'`) since that engine-specific enforcement mechanism has no PostgreSQL counterpart yet. **Not fully closeable until §12** ships role-revocation append-only enforcement — at that point those two tests' PostgreSQL equivalents need writing and should turn green rather than skip.
- [x] zero frontend work required to pass — the suite runs entirely through management commands + the public API
- [ ] the test is the CI gate for a seed release — mechanical CI wiring, deferred until §12 closes the loop above

## Security notes
- Step 6 must assert the absence of any update/delete path, not just that none was called — covered: ORM `.update()`/`.delete()`, instance `.delete()`, API DELETE/PUT/PATCH (401 — `PublicReadOnly` denies at the permission layer before DRF checks for a handler, so an unauthenticated write never reaches one), and raw SQL (SQLite guard trigger)

## Out of scope
- UI polish (§07/§08) — acceptance runs headless via the API

## Session handoff

### Why this isn't fully "done"
The one open item is §12: PostgreSQL append-only enforcement (role revocation) doesn't exist yet, so there's nothing for a PostgreSQL-specific guard-trigger-equivalent test to check. Both engines otherwise fully pass everything currently built. Re-visit this TODO once §12 ships that enforcement — write its PostgreSQL test, confirm it goes green (not skipped), then this can move to `done`.

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
None right now. Both legs pass everything currently buildable. Come back to this file once §12 ships PostgreSQL role revocation, add its test, confirm green, then mark `done`.
