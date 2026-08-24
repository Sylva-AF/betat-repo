# TODO 09 — Discoverability: announce & export

> Status: done — full test suite green on both SQLite (94/94) and PostgreSQL (92 passed + 2 expected skips)
> Blueprint: [§9](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Discoverability commands"
> Depends on: 05, 06 · Blocks: nothing

## Goal
Two push-side CLI commands as the accessibility valve for intermittent hosts — while pull-crawling stays primary and NO crawler ships in this package.

## Tasks
- [x] `betat announce` — POST to registry/reference index: "new records, crawl me now"; optional auto-run on accept
- [x] `betat export` — signed, integrity-verifiable dump of all records, submittable by any means
- [x] Export format: every record's `record_id` recomputes and matches
- [x] Confirm no crawler is introduced anywhere — nothing in this section reads/serves records beyond what §05/§06 already built; `export`/`announce` only push, never crawl

## Acceptance criteria
- [x] `export` output validates (all record_ids recompute)
- [x] `announce` posts correct payload (registry mockable in tests)
- [x] no crawler exists in the package

## Security notes
- Export signature covers record content; a tampered export fails verification — see handoff on what "signed" means here
- `announce` sends pointers/metadata only, never content

## Out of scope
- Building/running any index or crawler (index operators' job; betat main has its own)

## Session handoff

### Design decisions (full rationale in BLUEPRINT §09 Decision Log)
- **"Signed" means a recomputable SHA-256 bundle hash (`export_hash`), not an asymmetric digital signature.** No "community signing key" concept exists anywhere in this framework — identities belong to Provenanciers/institutions (§03), not the community itself, and `CommunityConfig` has no private-key field. Inventing one solely for `export` would be new, undecided infrastructure. Each record's own `record_id` already provides per-record integrity (same recomputation `store.verify_integrity()` does); `export_hash` extends that to the bundle as a whole. Real asymmetric bundle signing is future work, not silently substituted.
- **The registry's `announce` endpoint doesn't exist anywhere yet.** ARCHITECTURE.md's registry interface is explicitly "a sketch... to be refined by Contributors" and only lists `GET .../communities`, `GET .../communities/{id}`, `POST .../register` — no announce endpoint. `core/announce.py` POSTs a reasonable, documented payload (`community_id`, `store_uri`, `announced_at`) to a new `BETAT_REGISTRY_URL` setting, with **no default** — nothing honest to point it at until an operator has actually registered somewhere and a real contract exists. Expect this payload shape to need revisiting once the registry ships for real.
- **Optional auto-announce on accept is wired into `workflow/api/views.py`'s `ReviewView`**, gated by `BETAT_AUTO_ANNOUNCE` (default `False`). Best-effort only: wrapped in try/except, failures logged via `logging.getLogger(__name__).warning(...)` and never raised — a slow or unreachable registry must not block or fail an accept response. This modifies an already-shipped §04 file; additive and off-by-default, so no existing §04 test's behavior changes.
- **`export` reads `ProvenanceRecord.objects.all()` directly**, not `store.list_records()` — same precedent as §06 (reads don't need to route through store.py's minimal, paginated read API when the full unpaginated set is genuinely needed).
- Uses `urllib` (stdlib) for the registry POST, consistent with `bundledui/rendering.py`'s content-hash fetch — no new HTTP-client dependency.

### Files written this section
- `core/export.py`, `core/announce.py` — the reusable logic
- `core/management/commands/export.py`, `core/management/commands/announce.py`
- `betat_community/settings.py` — `BETAT_REGISTRY_URL`, `BETAT_AUTO_ANNOUNCE`
- `workflow/api/views.py` — optional best-effort auto-announce on accept
- `tests/test_discoverability.py` — new

### Closed out
Full suite green on both SQLite (94/94) and PostgreSQL (92 passed + 2 expected skips). Section done.
