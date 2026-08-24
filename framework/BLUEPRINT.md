# Betat Community Framework — Build Blueprint

> Status: seed · Authoritative build detail for [COMMUNITY_FRAMEWORK.md](../COMMUNITY_FRAMEWORK.md) v0.2
>
> **Authority hierarchy:** spec governs blueprint · blueprint governs TODOs · TODOs govern code.
> A conflict is resolved upward (the higher document wins); the fix flows downward in the same commit.
> When implementation discovers the blueprint is wrong, record it in the Decision Log **first**, then code.
>
> **Section numbers mirror the TODOs exactly.** Blueprint §NN ↔ [todos/NN](todos/). §0 is the whole-picture layer every session reads first.

---

## §0 — The Whole Picture (read first, every session)

### Locked build decisions (§0 session)

| # | Decision | Choice | Note |
|---|----------|--------|------|
| 1 | Environment / packaging | **plain venv + pip**; `pyproject.toml` defines the package | dev install: `pip install -e "./framework[dev]"` |
| 2 | API layer | **Django REST Framework** | serializers, token auth, pagination, browsable API |
| 3 | CLI | **thin `betat` console script → Django management commands** | zero extra dependency; every command also `manage.py <cmd>` |
| 4 | App decomposition | **six apps** nested in `betat_community/` | one app ↔ one TODO section |
| 5 | Python floor | **3.11**, tested through 3.12+ | 3.10 EOL ~Oct 2026; floor may rise by consensus |
| 6 | Tests | **pytest + pytest-django** | dev-only; plain asserts, fixtures |

### The tree — git root to a single app

```
betat-repo/                          ← git root · venv + pip here · public docs here
├── .venv/                           ← environment (gitignored)
├── README.md  *.md  _config.yml     ← manifesto + Jekyll site
├── CNAME  index.md  BLUEPRINT? (no — blueprint lives under framework/)
│
└── framework/                       ← THE PACKAGE (pip install -e ./framework)
    ├── pyproject.toml               ← package name, deps, [dev] extra, `betat` entry point
    ├── README.md                    ← package front door → points to BLUEPRINT.md
    ├── BLUEPRINT.md                 ← this file
    ├── TODO.md  todos/              ← build plan
    ├── manage.py                    ← Django entry (dev/admin)
    ├── tests/                       ← pytest suite, one module per app
    │
    └── betat_community/             ← THE DJANGO PROJECT (importable)
        ├── __init__.py
        ├── settings.py              ← DRF, INSTALLED_APPS, SQLite default
        ├── urls.py                  ← mounts each app's routes
        ├── wsgi.py / asgi.py
        ├── cli.py                   ← `betat` dispatcher (§1)
        ├── common/                  ← cross-app shared code (plain package, NO models)
        │   ├── permissions.py       ← public-read / authenticated-write split
        │   ├── serializers.py       ← shared provenance record serializer base
        │   ├── errors.py            ← the standard error shape
        │   └── hashing.py           ← canonicalization (shared with store)
        ├── core/                    ← §01/§02 config + community identity
        ├── store/                   ← §05 append-only provenance store
        ├── communityauth/           ← §03 auth plugins + floor
        ├── workflow/                ← §04 submit / review / accept
        ├── federation/              ← §06 /betat/ public endpoints
        └── bundledui/               ← §07 Django-template UI

    each app: models.py + apps.py + migrations/ + api/{views,serializers,mixins}.py
```

Everything past the git-root level is authoritative here and nowhere else; `framework/README.md` only signposts to this section.

### The API URL table (the mandatory contract)

| Method | Path | Auth | App / section | Purpose |
|--------|------|------|---------------|---------|
| GET | `/betat/info` | none | federation §06 | community identity + declared standard |
| GET | `/betat/records` | none | federation §06 | paginated records, newest first (`?hi_only=`) |
| GET | `/betat/records/{id}` | none | federation §06 | one record |
| GET | `/betat/changes?since=` | none | federation §06 | incremental feed for crawlers |
| POST | `/betat/enroll` | none→identity | communityauth §03 | apply/enroll a Provenancier |
| POST | `/betat/submit` | Provenancier token | workflow §04 | submit a contribution |
| GET | `/betat/queue` | verifier | workflow §04 | pending review queue |
| POST | `/betat/review/{id}` | verifier | workflow §04 | accept or reject → writes record on accept |

Reading endpoints are public and unauthenticated — always. Writing endpoints require the stated role. The bundled UI consumes only this table; if the UI needs something the table lacks, the table is incomplete.

### Data flow (one accepted contribution)

```
betat init → core writes CommunityConfig (id = FQDN, declared standard ≥ baseline)
   │
Provenancier → POST /enroll → communityauth (≥1 protocol-list method) → identity
   │
POST /submit → workflow: Submission(pending) — content_ref + hash only, never content
   │
GET /queue → verifier → POST /review/{id}
   │
   ├── reject → Submission(rejected), no record
   └── accept → workflow builds record → store.append():
                 canonicalize → SHA-256 record_id → INSERT (no update/delete path)
   │
GET /records, /records/{id}, /changes → federation serves them publicly
   │
crawler/index reads federation → renders per RENDERING.md (badge, standard, integrity states)
```

### Conventions (all sections obey)

- **Naming:** apps lowercase single word; models `PascalCase`; DRF serializers `<Model>Serializer`; management commands the verb only (`init`, `runserver`, `check`, `announce`, `export`).
- **Error shape:** every API error returns `{"error": {"code": "<machine_code>", "message": "<human text>"}}` with the right HTTP status. One shape everywhere.
- **Settings:** one `settings.py`; environment overrides via env vars (`BETAT_DB`, `BETAT_SECRET_KEY`); SQLite default requires no env at all.
- **Tests:** `framework/tests/test_<app>.py`; pytest, plain asserts; every acceptance-criterion line in a TODO maps to at least one test.
- **Spec-permanent names never change:** `hi_tag`, `provenancier`, and the PROVENANCE_SPEC field names are fixed by the spec's versioning rules.
- **Definition of done includes docs:** a public capability without a usage snippet is unfinished (COMMUNITY_FRAMEWORK.md, Documentation Standard).
- **API layer structure (per-app `api/` + project `common/`).** Each app separates its API layer into an `api/` sub-package (`<app>/api/views.py`, `serializers.py`, `mixins.py`) rather than app-root `views.py`/`serializers.py` — keeping the data layer (`models.py`) and API layer distinct as they grow, while preserving one-app-per-section alignment (a session on §NN still works inside one app folder). Cross-app shared code lives in a project-level `betat_community/common/` package: `permissions.py` (public-read / authenticated-write split), `serializers.py` (shared provenance record serializer base), `errors.py` (the standard error shape), `hashing.py` (canonicalization, shared with `store`). Rule of thumb: used by one app → that app's `api/`; used by two or more → `common/`. **Never import from another app's `api/`;** shared needs go through `common/`. `common/` and every `api/` are plain Python packages — no `apps.py`, not in `INSTALLED_APPS`, and (critically) `common/` holds **no models**. Data-shaped cross-cutting needs that require models get their own purpose-named app when they arise (e.g. a future `registry` or `attestation` app), never a catch-all `common` app and never speculatively pre-built — this is a deliberate departure from platform patterns (e.g. an events/media `common` app) that do not fit Betat, since Betat never hosts content and never tracks readers.
- **Database-agnostic by construction (dual-DB ship promise).** The framework must run identically on SQLite (seed/default) and PostgreSQL (production) with no change beyond database settings — an end user goes to production by pointing settings at PostgreSQL, nothing more. Use the Django ORM and migrations everywhere; do NOT write engine-specific SQL. The ONE sanctioned exception is the append-only enforcement seam, where the mechanism legitimately differs by engine: SQLite guard triggers vs PostgreSQL role-permission revocation. Engine-specific code anywhere outside that seam is a defect against the ship promise. The founder verifies the store and acceptance suites pass on BOTH engines before shipping.

---

## §1 — Project Scaffold & CLI

**Owns:** `pyproject.toml`, `betat_community/settings.py`, `urls.py`, `cli.py`, `manage.py`, package skeleton.
**Detail:** `pyproject.toml` declares name `betat-community`, Python `>=3.11`, deps `django>=5,<6`, `djangorestframework`; `[dev]` extra adds `pytest`, `pytest-django`. Console entry point `betat = "betat_community.cli:main"`. `cli.py` is a thin dispatcher: it parses the first token (`init`, `runserver`, `check`, `announce`, `export`) and delegates to the matching Django management command, so each is independently runnable as `python manage.py <cmd>`. `settings.py` installs DRF and the six apps; database defaults to SQLite at `BETAT_DB` or `./betat.sqlite3`.
**Acceptance:** `pip install -e "./framework[dev]"` succeeds; `betat --help` lists commands; `pytest` runs (zero tests OK); `manage.py check` passes.

## §2 — Config & Community Identity

**Owns:** `core/` — `CommunityConfig` model, ID validation, `betat init` command.
**Detail:** `CommunityConfig` fields per COMMUNITY_FRAMEWORK.md (id, name, domain, content_type, hi_standard, auth_methods, store_uri). ID validator: lowercase FQDN, syntactically valid, non-empty labels. `init` renders the baseline standard (`human-originated, community-verified`) and accepts strengthen-only additions; declares (does not verify) domain control; prints the readiness checklist and the "next steps / verification happens at the registry" note. Single-config-per-install for seed.
**Acceptance:** `betat init` writes a valid config; a malformed ID is rejected with the standard error shape; baseline is present and can only be extended; `/betat/info` (once §06 exists) serves it.

## §3 — Authentication Plugins & Floor

**Owns:** `communityauth/` — `AuthMethod` base, three seed plugins, the floor enforcement, `/enroll`.
**Detail:** `AuthMethod` protocol with `enroll()` / `authenticate()`. Seed plugins: `PeerVouchAuth`, `CryptoKeyAuth`, `InstitutionalAuth`. **Floor rule enforced in config load:** at least one method from the protocol list must be configured; a config with zero, or with a non-listed method, fails to start. Chosen method(s) recorded so every record can carry `provenancier.authentication_method`. Government-ID and behavioral attestation are roadmap stubs, not shipped.
**Acceptance:** each seed plugin enrolls and authenticates in tests; a zero-method config is rejected at startup; a non-listed method is rejected; the method name propagates into a built record.

## §4 — Submission & Verification Workflow

**Owns:** `workflow/` — `Submission` model, `/submit`, `/queue`, `/review/{id}`, record building. API code in `workflow/api/`; the record serializer base and canonicalization come from `common/` (shared with store/federation).
**Detail:** `submit()` requires an authenticated identity and takes `content_ref` (URI/DOI/IPFS) + `content_hash` — never content itself; status `pending_review`. `review()` records verifier identity + timestamp; accept path calls `build_record()` then `store.append()`; reject path closes the submission with no record. `build_record()` composes a PROVENANCE_SPEC v0.1 record: declared standard into `declaration.custom_addition`, `hi_tag=true`, verification block filled.
**Acceptance:** unauthenticated submit is refused; accept produces a spec-valid record in the store; reject produces none; verifier identity + timestamp appear in the record.

## §5 — Append-Only Provenance Store

**Owns:** `store/` — `ProvenanceRecord` model, `canonical.py`, `store.py`, guard-trigger migration.
**Detail:** see [todos/05-provenance-store.md](todos/05-provenance-store.md) (the exemplar). Canonicalization: `record_id`/`record_signature` set to `""`, keys sorted, no whitespace, `json.dumps(..., sort_keys=True, separators=(",",":"))`; `record_id` = SHA-256, computed server-side always. `append/get/list/verify_integrity` only — no `update`/`delete` methods exist. SQLite `BEFORE UPDATE`/`BEFORE DELETE` triggers `RAISE(ABORT)` via migration (defense-in-depth, honestly weaker than role separation). Reject any record whose `hi_tag` is not `true`.
**Acceptance:** record round-trips byte-identical; `verify_integrity` passes clean / fails on tamper; raw `UPDATE`/`DELETE` fails on SQLite; `hi_tag:false` rejected.

## §6 — Federation Endpoints

**Owns:** `federation/` — the four public GET endpoints, DRF serializers, pagination. API code in `federation/api/`; record serializer base from `common/serializers.py`, the public-read permission from `common/permissions.py`.
**Detail:** `/betat/info` serves `CommunityConfig`; `/betat/records` paginated newest-first with `?hi_only=`; `/betat/records/{id}` one record; `/betat/changes?since=` incremental by timestamp. All public, unauthenticated, JSON, read-only. Serializers expose exactly the record schema — no internal fields leak.
**Acceptance:** all four return valid JSON; a written record appears at `/records` and `/records/{id}`; `since=` filters correctly; no endpoint requires auth; acceptance-test step 7 (independent crawler) passes.

## §7 — Bundled Minimal UI

**Owns:** `bundledui/` — Django templates: enroll, submit, review queue, public records list + record detail. (Templates + views live in `bundledui/`; it consumes the public API only. Its `api/` folder is unused unless it exposes endpoints — UI templates are not the API layer.)
**Detail:** server-rendered Django templates, no build step, no Node. **Consumes the public JSON API only** — no ORM shortcuts. Renders per [RENDERING.md](RENDERING.md), and its **integrity-state rules are binding**: validate `record_id` (tampered state), render the three content-hash states honestly, always show the declared standard beside the HI badge, always link the full record, render absence as *unverified* (never "fake"/"machine-made").
**Acceptance:** the four views work from a fresh install with zero frontend work; each view's data comes through the API; a tampered/changed/unreachable fixture renders its correct state; the evidence link resolves.

## §8 — Post-Install Seed Website

**Owns:** the first-run landing page + readiness checklist (in `bundledui/` or `core/`).
**Detail:** Django-style first-run page listing the four readiness items (robust DB engine; provenance assertions/records; authentication method; UI bundle), each linking its docs page, each showing outstanding/done state. Not decorative — reflects real config state.
**Acceptance:** fresh install shows the page with correct outstanding states; items link to docs; state updates as the operator completes each.

## §9 — Discoverability: `announce` & `export`

**Owns:** `betat announce` and `betat export` management commands.
**Detail:** `announce` pings the registry/reference index ("new records — crawl me now"), optionally auto-run on accept. `export` produces a signed, integrity-verifiable dump submittable by any means when live crawling isn't practical. **No crawler ships in this package** — crawling is the index operator's job. Pull remains primary; these are the accessibility valve for intermittent hosts.
**Acceptance:** `export` output validates (every `record_id` recomputes); `announce` posts the correct registry payload (mockable); neither introduces a crawler.

## §10 — Acceptance Test (the seven steps)

**Owns:** `tests/test_acceptance.py` — the end-to-end scenario from COMMUNITY_FRAMEWORK.md.
**Detail:** scripts the seven steps (init+declare → enroll → submit → review/accept → valid record with hi_tag+standard → served & integrity-verified & unmodifiable → independent crawler reads it). Runs as soon as §06 exists, then re-runs after every section. This is the seed-release gate.
**Acceptance:** all seven pass on a fresh SQLite install with zero frontend work.

## §11 — Documentation Site

**Owns:** the readthedocs-style docs (snippet per capability), per the Documentation Standard.
**Detail:** every endpoint, function, and CLI command gets a copyable example with real output. Readiness-checklist items deep-link here. PR rule: public behavior change must update its docs page (definition of done).
**Acceptance:** every §1–§9 public capability has a runnable snippet; the checklist links resolve into the docs.

## §12 — Packaging & Production Guide

**Owns:** final `pyproject.toml` polish, the "Recommended production stack" guide, PostgreSQL migration path.
**Detail:** build/verify the installable package; write the PostgreSQL guide — install, configure, **role setup: app role INSERT/SELECT only, UPDATE/DELETE revoked** (the real append-only boundary), and the SQLite→PostgreSQL migration route. Document the 3.11 floor and 3.12+ testing.
**Acceptance:** clean `pip install` from a built artifact works; the PostgreSQL guide runs end-to-end; append-only holds at the DB-permission level on PostgreSQL.

---

## Decision Log (append-only)

- **2026-07 · §0 locked (six decisions):** venv+pip; DRF; thin-dispatcher CLI; six nested apps; Python 3.11 floor; pytest. Rationale: boring-majority + widest-pool accessibility + one-app-per-TODO alignment. Superseded 3.10 (EOL) as a floor candidate.
- **2026-08 · API structure (per-app `api/` + project `common/`):** adopted while views were still empty (only models built in §1–§5), the cheapest moment. Each app gets `api/{views,serializers,mixins}.py`; cross-app behavioral utilities (permissions, shared serializers, error shape, canonicalization) live in `betat_community/common/` — a plain package with NO models, NOT in INSTALLED_APPS. Applied going forward from §6; §1–§5 (models-only, minimal API code) migrate lazily when touched. No cross-app `api/` imports; shared needs go through `common/`. Future data-shaped shared needs get purpose-named apps (`registry`, `attestation`), never a catch-all `common` app — a deliberate non-adoption of the events/media `common`-as-app pattern, which conflicts with Betat's never-host-content and never-track-readers principles. Amended §0 tree + conventions.
- **2026-08 · dual-database ship promise:** framework must pass store + acceptance suites on both SQLite (seed default) and PostgreSQL (production) before shipping; end users go to production by switching database settings only. Database-agnostic via ORM; sole engine-specific seam is append-only enforcement (SQLite triggers / PostgreSQL role revocation). Amended BLUEPRINT §0 conventions, TODO 10, TODO 12.

- **2026-08 · §03 — how many members must vouch for a new person (peer-vouch threshold).** One way a community verifies someone is a real human is "peer vouching": existing members confirm the newcomer is genuine. The question is how many members must vouch before the person is accepted. Default is **2**, and it is a setting each community can raise (never lower). Why not 1: if a single member could admit anyone, one careless or dishonest member could wave in a crowd of fake accounts — and because each would carry the "verified human" (HI) tag, that would quietly poison the trust the whole system depends on. Requiring at least two people makes that much harder. This is the strength of the weakest method on the authentication floor, so it is a deliberate, visible choice, not a silent default.

- **2026-08 · §03 — the authenticated "identity" object must match the record's format.** When someone is authenticated, the code produces an identity object (who they are, how they were verified). That object is not only used internally — its details are copied into the permanent provenance record (the `provenancier` section defined in PROVENANCE_SPEC.md: identity, identity_type, authentication_method, display_name). So the identity object must carry exactly those fields, named the same way. Shape it against the spec's `provenancier` block from the start, so nothing has to be reworked when §04 (workflow) builds the actual record from it.

- **2026-08 · §03 — floor enforcement runs as a Django system check, not an `AppConfig.ready()` DB query.** `communityauth/checks.py` registers via the System Check Framework, wired in `communityauth/apps.py`'s `ready()`. Checks run automatically before `runserver`/`migrate`/`manage.py check`; the check function queries `CommunityConfig` defensively (swallows `OperationalError`/`ProgrammingError` for a pre-migration DB, no-ops with no config yet) rather than querying at import time, which would risk breaking `makemigrations` on a fresh install.
- **2026-08 · §03 — `CryptoKeyAuth`/`InstitutionalAuth` use real Ed25519 verification, no replay protection.** `communityauth/crypto.py` wraps the `cryptography` package (PyCA) for `verify()`/`sign()`/`generate_keypair()` — not hand-rolled. `CryptoKeyAuth.enroll()` requires a self-signed proof-of-possession (applicant signs their own public key), keeping enrollment stateless. Both plugins' `authenticate()` take a caller-supplied message + signature with **no replay protection** — the caller must include a fresh nonce/timestamp in what they sign. Deliberate seed-implementation simplification; document it prominently when §11 (docs) happens.
- **2026-08 · §03 — `CommunityConfig` gains `peer_vouch_threshold` and `trusted_institutions`.** `peer_vouch_threshold` (int, default 2, `MinValueValidator(2)`) backs the peer-vouch threshold decision above. `trusted_institutions` (JSONField, `{institution_id: public_key_hex}`) is `InstitutionalAuth`'s trust table — `authenticate()` re-verifies against its *current* value, so an institution removed or rekeyed after enrollment stops authenticating that institution's previously-enrolled members. Both fields live on `CommunityConfig` (the single per-install config object) rather than a separate model, consistent with §02's single-config-per-install assumption.
- **2026-08 · §03 — `core.validate_auth_methods` now imports `communityauth.floor.validate_floor`.** Closes the gap §02 deliberately left open (protocol-list membership wasn't checkable until §03 existed). The import is lazy (inside the function, not at module top) to avoid an app-load-order dependency between `core/models.py` and `communityauth/models.py`. This is the one sanctioned `core`→`communityauth` model-validation dependency; it does not license further cross-app model imports elsewhere.

- **2026-08 · §04 — a "verifier" is a Django staff user (`is_staff=True`).** Neither COMMUNITY_FRAMEWORK.md nor PROVENANCE_SPEC.md defines a Verifier model — the spec's `review(submission, verifier)` sketch leaves the role's shape open, and `verified_by` is documented only as "identity of verifier." Rather than invent a new identity model parallel to Provenancier, verifiers are plain Django staff users, managed through the admin panel the framework already promises ("An admin panel for the community's own verifiers and governance," COMMUNITY_FRAMEWORK.md). `workflow/api/mixins.py`'s `IsVerifier` permission checks `request.user.is_staff`; `verification.verified_by` in a built record is the staff account's `username`. A verifier need not also be an enrolled Provenancier — governance and contribution are separate roles.
- **2026-08 · §04 — `verification.method` is fixed to `'editorial_review'`.** Of PROVENANCE_SPEC's five Verification Methods, `editorial_review` ("A designated community editor reviewed and accepted") is the only one that matches what this framework actually builds: a staff verifier accepting via `/betat/review/{id}`. The other four (`community_peer_review`, `institutional_endorsement`, `cryptographic_signature`, `self_declared_authenticated`) describe workflows this seed doesn't implement — not selectable at review time, to avoid a record claiming a verification method that didn't actually happen.
- **2026-08 · §04 — `content_type` is not a submit-time input.** A community is authorized to verify exactly one content type (`CommunityConfig.content_type`, singular per §02's single-config-per-install assumption) — accepting it from the submitter would just be a value to validate against `config.content_type` anyway (store.py already enforces `content.type == community.content_type`). `build_record()` reads `config.content_type` directly; `Submission` carries no `content_type` field. The JS snippet in COMMUNITY_FRAMEWORK.md's Layer 1 example includes a `content_type` key — that snippet is explicitly illustrative ("teaches the access model"), not a literal wire-format spec.
- **2026-08 · §04 — `declaration_accepted` must be exactly `true` at submit, or the submission is refused (400), not stored.** Betat Baseline item 3 ("Declaration signed") requires the declaration be accepted *at submission*; deferring that check to review time would let a Submission exist that never actually had the declaration accepted. `Submission.declaration_accepted` is kept as a stored field (always `true` once a row exists) for audit-trail completeness, not as a gate checked later.

- **2026-08 · §06 — `/betat/records` and `/betat/changes` read `store.models.ProvenanceRecord` directly via DRF's standard `generics.ListAPIView` + `PageNumberPagination`, not through `store.py`'s `list_records()`.** `store.py`'s own docstring frames it as "the sole write and read API," but that described what existed for §04's single-append use case, not a mandate that every future read path must route through hand-rolled wrapper functions. The append-only guarantees (guard triggers, blocked `update()`/`delete()`) only constrain writes — a plain `SELECT` via the ORM touches none of them. Reimplementing DRF's pagination (count/next/previous, page_size query param, bounds) by hand inside `store.py` would be strictly more code for a worse result than the framework already provides. `store.get()` is still used for the single-record lookup (`/betat/records/{id}`) — that one's already the right minimal primitive and needed no reimplementation.
- **2026-08 · §06 — `common/serializers.py`'s `ProvenanceRecordSerializer` declares no fields; `to_representation()` delegates to `ProvenanceRecord.to_dict()`.** Re-declaring PROVENANCE_SPEC's record shape field-by-field a second time would create two places that must stay in sync as the spec evolves. `to_dict()` is already the tested, canonical shape (the same method `store.verify_integrity()` hashes) — delegating makes drift impossible instead of merely unlikely.
- **2026-08 · §06 — `/betat/info` exposes exactly `CommunityConfig`'s spec-defined fields** (`id`, `name`, `domain`, `content_type`, `hi_standard`, `auth_methods`, `store_uri` — matching COMMUNITY_FRAMEWORK.md's "Community configuration" sketch). `peer_vouch_threshold` and `trusted_institutions` (§03 additions) are operational config for the authentication floor, not part of the community's public identity, and stay internal.
- **2026-08 · §06 — `/betat/info` with no `CommunityConfig` yet returns 404 `not_configured`, not 503.** §03/§04's write endpoints (`/enroll`, `/review`) use 503 for a missing config because a write genuinely can't be serviced yet. `/betat/info` is a GET on what is conceptually a singleton resource — before `betat init`, that resource simply doesn't exist, which is standard 404 semantics. Same error `code` across all four (`not_configured`) for grep-ability; the HTTP status varies by GET/POST semantics.

- **2026-08 · §10 — step 2 (enrollment) uses `CryptoKeyAuth`, not `PeerVouchAuth`.** `PeerVouchAuth` needs `peer_vouch_threshold` (default 2) already-enrolled members to vouch — on a genuinely fresh install there are none, so peer-vouch can't bootstrap the very first Provenancier. `CryptoKeyAuth`'s self-signed proof-of-possession has no such dependency, matching the acceptance test's actual scenario: a brand-new community's first-ever enrollment.
- **2026-08 · §10 — the PostgreSQL leg of the dual-DB acceptance criterion is blocked, not skipped-and-forgotten.** As originally written, `settings.py`'s `DATABASES` hardcoded `ENGINE: django.db.backends.sqlite3` with no way to point at Postgres at all. **Update (same day):** the developer added two commented-out Postgres `DATABASES` blocks directly in `settings.py` — `betatdb` (a production-shaped config) and `betat_testdb` (for running the suite against Postgres), each with inline credentials rather than env vars, uncommented one-at-a-time as needed. This is a deliberate dev-only convenience (no secrets needed in `.env` for local work) and diverges from BLUEPRINT §0's stated "environment overrides via env vars (`BETAT_DB`)" convention — worth reconciling when §12 documents the real production path, but not a blocker for now. **Update (same day, 2):** added `psycopg[binary]>=3` to `pyproject.toml` dependencies (developer chose psycopg3 over psycopg2 when asked) — uncommenting either Postgres block plus `pip install -e "./framework[dev]"` is now enough to actually connect. One thing still needed before the suite can *pass* against Postgres: append-only enforcement (role INSERT/SELECT-only, UPDATE/DELETE revoked) still doesn't exist — that remains §12's job. `tests/test_acceptance.py` is written engine-agnostically already (only the SQLite-guard-trigger assertion is gated on `connection.vendor`, and that gate does NOT skip the rest of the test) so it should pass steps 1–5 and 7 against Postgres today, and should pass step 6's engine-specific check too once §12 lands.
- **2026-08 · §10 — Postgres credentials committed in plaintext to `settings.py` (`betuser`/`panda#1`, `betester`/`alltest#1`).** Recorded as a deliberate, acknowledged dev-only choice (see above), not an oversight — flagging here so a future session doesn't "fix" it by silently rewriting it, and so it gets revisited explicitly when §12 documents the real production credential story (env vars, secrets manager, etc. — production must not inherit this pattern).
- **2026-08 · §10 — found and fixed a §03 bug while building step 2: `EnrollView` never checked `method` against `CommunityConfig.auth_methods`, only against the global `PROTOCOL_LIST`.** A community that enabled only `cryptographic_signature` would have silently also accepted `community_peer_vouching` enrollments, since that method exists elsewhere on the protocol list. Fixed in `communityauth/api/views.py` (`method_not_enabled` rejection) with a regression test in `test_communityauth.py`; §03 stays marked done since this was a live-but-narrow gap, not a rebuild, but noted here since the fix landed in a file BLUEPRINT already described as finished.

- **2026-08 · §01/§02 — `init.py` grew operator-accountability steps on top of §02's `CommunityConfig`-writing logic ("Option C"); a database-engine choice was considered and deliberately deferred.** A same-day amendment proposal argued `betat init` was a "missed task" from TODO 01 and suggested rebuilding it around `.env` instead of the database — inaccurate against the repo (§02 already shipped a tested, `CommunityConfig`-writing `init`, load-bearing for every section since: §03 `EnrollView`, §04 `ReviewView`, §06 `InfoView`, the §10 acceptance test all call `CommunityConfig.objects.first()`/`.get()`). Resolved by keeping `CommunityConfig` as the sole operational source of truth and layering the amendment's genuinely useful parts on top instead of replacing it: environment preflight (Python/SQLite availability), a DNS-resolution check on the declared community id, an operator good-faith declaration, a contact email, and an `.env` accountability record (`BETAT_OPERATOR_EMAIL`, `BETAT_DECLARATION_ACCEPTED`, `BETAT_DECLARED_COMMUNITY_ID`) — all additive, all deliberately unbypassable even non-interactively (anti-automation is the point: a script can't fabricate a resolving domain or a real operator's acceptance). This version is live and its tests pass on both SQLite and PostgreSQL (§10) — `test_core.py`/`test_acceptance.py` mock `input()` to answer as a real operator would, rather than the command growing a bypass flag.
  A separate, related idea — an interactive SQLite/PostgreSQL choice inside `init`, writing `BETAT_DB` to `.env`, read by a `dj_database_url`-driven `settings.py` `DATABASES` block — was reviewed and **deliberately not built**: "let's forget about the db option for now, maybe when users complain in the future we bring this in through a framework update or a patch." Worth knowing for whoever picks this up later: it's not just a UI addition — choosing PostgreSQL mid-wizard and writing `BETAT_DB` to `.env` doesn't retroactively move the *current* process's DB connection (Django reads `DATABASES` once at startup), so anything that same `init` run writes to `CommunityConfig` would land in the old engine, not the newly-chosen one. A real implementation needs to resolve that sequencing (likely: DB choice before `CommunityConfig` creation, with the operator re-running `init` after `migrate` against the new engine). `dj-database-url` and `python-dotenv` are already in `pyproject.toml` dependencies (added in anticipation) — no need to re-add them when this is picked up.

- **2026-08 · §07 — the bundled UI calls its own public API through Django's `test.Client`, not real HTTP sockets.** Satisfies "consumes the public JSON API only — no internal shortcuts" (COMMUNITY_FRAMEWORK.md) genuinely: same URLconf, serializers, and permission classes any external caller hits. A real socket back to the same process risks deadlock behind a single-threaded server and would add an HTTP-client dependency for no benefit. One correctness detail this required: `Client()` defaults to `Host: testserver`, which only passes `ALLOWED_HOSTS` inside pytest's test-environment setup, not in a real running server — every `bundledui` view constructs `ApiClient(server_name=request.get_host())` so the internal call reuses whatever host the browser's own request already passed validation for.
- **2026-08 · §07 — Provenanciers "log in" via a server-side session holding their enroll token; there is no separate returning-provenancier login flow.** Provenanciers are created with an unusable password (§03 design, token-only auth) — there's nothing to log back in with via a username/password form. `CryptoKeyAuth`'s `authenticate()` exists for re-deriving an identity from credentials, but a browser form can't reasonably ask a human to produce a fresh signature without client-side JS signing, which the bundled UI deliberately doesn't ship. Accepted as a known, honest gap for the seed implementation (enroll-then-immediately-submit-in-the-same-session is what the acceptance test and a first-run operator actually do) rather than solved here — a roadmap item, not an oversight.
- **2026-08 · §07 — verifiers use real Django session login (they have real passwords via `createsuperuser`), with a DRF token auto-provisioned on first `bundledui` use.** `Token.objects.get_or_create(user=request.user)` in `views._verifier_token()` is the one direct ORM touch in this app — deliberately scoped to token bootstrapping for an already-session-authenticated user, not a business-logic shortcut; no view here ever touches `Submission`/`ProvenanceRecord`/`CommunityConfig` directly.
- **2026-08 · §07 — `record_id` tampering is validated on every record render; `content_hash` re-verification (fetching `content.location` and hashing it) only happens on the record-detail page, not the records list.** The first is a cheap local recomputation (reuses `common/hashing.py` rather than reimplementing it) and RENDERING.md's binding rule doesn't distinguish by view, so it applies everywhere a record is shown. The second is a live external fetch; RENDERING.md explicitly allows "periodic or on-view," and re-fetching every record's content on every paginated list load would be slow and network-heavy for exactly the low-bandwidth operators COMMUNITY_FRAMEWORK.md's discoverability section says this project cares about.
- **2026-08 · §07 — color system is driven by RENDERING.md's honesty rules, not visual taste.** HI badge: one constant brand color, never reused for state signaling. Verified: quiet/subdued (the expected default). Changed: amber, never red — RENDERING.md is explicit that a hash mismatch is "changed," never "fake." Unreachable and unverified/absent: both neutral gray, deliberately not alarming ("the record remains valid," "absence of proof, not an accusation"). Tampered (`record_id` mismatch): the *only* red/danger state — the one case actually proven bad. One hand-written stylesheet, no CDN/vendored framework, consistent with "deliberately plain" and zero added runtime dependency for low-bandwidth operators.
- **2026-08 · §07 — UI paths live under `/community/`, not `/`.** Avoids colliding with `/betat/` (the API surface) and deliberately doesn't claim the root path, which belongs to §08's first-run landing page.

- **2026-08 · §08 — the landing/readiness page checks `connection.vendor` directly rather than routing through the public API, unlike §07's four views.** It's an operator/ops status page, not part of the Layer 2 "bundled UI consumes the public API only" consumption model that rule targets — and the DB engine is infrastructure state that has no legitimate reason to be exposed on any public API (unlike provenance records, which are the API's whole purpose). The "is this install configured" half of the checklist still goes through `ApiClient`/`/betat/info`, since that part genuinely is API-shaped data.
- **2026-08 · §08 — doc links are a placeholder (`https://betat.org`), not real per-item deep links.** §11 (documentation site) doesn't exist yet, so there is nowhere honest to point four distinct URLs at. `views.py`'s `DOCS_PLACEHOLDER` constant marks exactly where real per-item links go once §11 ships.
- **2026-08 · §08 — only two of the four readiness items are actually distinguishable by current config state.** "Provenance records" and "auth method" both resolve to the same fact (`CommunityConfig` exists with non-empty `auth_methods` — the model has no partial/staged configuration state), so they always move together. "UI bundle" is always `DONE` — the bundled UI ships by definition, there's no partial-install state for it to reflect. This is an honest reflection of what the codebase can distinguish today, not a shortcut or fabricated granularity.

- **2026-08 · §09 — `export`'s "signed" means a recomputable SHA-256 bundle hash (`export_hash`), not an asymmetric digital signature.** No "community signing key" concept exists anywhere in this framework — identities belong to Provenanciers/institutions (§03), not the community itself, and `CommunityConfig` has no private-key field. Inventing one solely for `export` would be new, undecided infrastructure with nowhere to store or manage it. Each record's own `record_id` already provides per-record integrity (the same recomputation `store.verify_integrity()` performs, via `common/hashing.py`); `export_hash` extends the same idea to the bundle as a whole so a reader can detect if the export file itself was altered in transit. Real asymmetric bundle signing is future work, not silently substituted for.
- **2026-08 · §09 — `announce` POSTs to a new `BETAT_REGISTRY_URL` setting with no default, since the registry's own announce contract doesn't exist yet.** ARCHITECTURE.md's registry interface sketch is explicitly "to be refined by Contributors" and only lists `GET .../communities`, `GET .../communities/{id}`, `POST .../register` — no announce endpoint. `core/announce.py` POSTs a reasonable, documented payload (`community_id`, `store_uri`, `announced_at`); expect this shape to need revisiting once a real registry contract ships. Uses `urllib` (stdlib), consistent with `bundledui/rendering.py`'s content-hash fetch — no new HTTP-client dependency.
- **2026-08 · §09 — optional auto-announce on accept is wired into `workflow/api/views.py`'s `ReviewView` (§04), gated by `BETAT_AUTO_ANNOUNCE` (default `False`).** Best-effort only: wrapped in try/except, failures logged (`logging.getLogger(__name__).warning`) and never raised into the response — a slow or unreachable registry must not block or fail an accept. Modifies an already-shipped §04 file; additive and off-by-default, so no existing §04 test's behavior changes. Noted here since the change landed in a file BLUEPRINT already described as finished, same pattern as the §10 `EnrollView` fix.
- *(future deviations append here — record before coding the change)*

---

*Build plan: [TODO.md](TODO.md) · Session bootstrap: [CLAUDE.md](CLAUDE.md) · Spec: [COMMUNITY_FRAMEWORK.md](../COMMUNITY_FRAMEWORK.md)*
