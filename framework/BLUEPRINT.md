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
- *(future deviations append here — record before coding the change)*

---

*Build plan: [TODO.md](TODO.md) · Session bootstrap: [CLAUDE.md](CLAUDE.md) · Spec: [COMMUNITY_FRAMEWORK.md](../COMMUNITY_FRAMEWORK.md)*
