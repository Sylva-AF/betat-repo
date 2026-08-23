# TODO 06 — Federation Endpoints

> Status: done — all acceptance criteria pass (full test suite green)
> Blueprint: [§6](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Federation endpoints"
> Depends on: 02, 05 · Blocks: 07, 10

## Goal
The `federation` app: the community's public face — four read-only JSON endpoints any registry, crawler, or index can call without authentication.

## Tasks
- [x] `GET /betat/info` → `CommunityConfig` (identity + declared standard)
- [x] `GET /betat/records` → paginated, newest-first; `?hi_only=` filter
- [x] `GET /betat/records/{id}` → one record
- [x] `GET /betat/changes?since=` → records after a timestamp (incremental crawl)
- [x] DRF serializers exposing exactly the record schema — no internal fields leak
- [x] Pagination + consistent ordering

## Acceptance criteria
- [x] all four return valid JSON, unauthenticated
- [x] a written record appears at `/records` and `/records/{id}`
- [x] `since=` filters correctly
- [x] no endpoint requires auth
- [ ] acceptance-test step 7 (independent crawler, host address only) — deferred to §10, out of scope here

## Security notes
- Read-only: no POST/PUT/DELETE on this surface
- Serializers must not expose internal DB ids or non-spec fields

## Out of scope
- Writing records (§04)
- Crawling (never in this package — index operators crawl)

## Session handoff

### Design decisions (logged in BLUEPRINT.md §06 Decision Log — read there for full rationale)
- **Reads bypass `store.py`'s `list_records()`** — `/records` and `/changes` query `ProvenanceRecord` directly via DRF's `generics.ListAPIView` + `PageNumberPagination` (correct count/next/previous for free). `store.get()` is still used for the single-record lookup.
- **`common/serializers.py`'s `ProvenanceRecordSerializer` has no declared fields** — `to_representation()` delegates to `ProvenanceRecord.to_dict()` so the wire shape can never drift from the model's own canonical shape.
- **`/betat/info` excludes `peer_vouch_threshold`/`trusted_institutions`** (§03 additions, not part of the spec's `CommunityConfig`).
- **`/betat/info` 404s (not 503) when unconfigured** — GET-on-a-singleton semantics, distinct from write endpoints' 503.
- New this section: `common/permissions.py` (`PublicReadOnly`) and `common/serializers.py` (`ProvenanceRecordSerializer`) — both were named in BLUEPRINT §0's `common/` convention since §0 but never built until now; later apps should reuse them rather than re-inventing.

### Files written this section
- `common/permissions.py` — `PublicReadOnly`
- `common/serializers.py` — `ProvenanceRecordSerializer`
- `federation/api/pagination.py` — `RecordPagination`
- `federation/api/serializers.py` — `CommunityConfigSerializer`
- `federation/api/views.py` — `InfoView`, `RecordsView`, `RecordDetailView`, `ChangesView`
- `betat_community/urls.py` — mounts `/betat/info`, `/betat/records`, `/betat/records/<str:record_id>`, `/betat/changes`
- `framework/tests/test_federation.py` — new, 10 tests covering every acceptance criterion above plus hi_only filtering, no-internal-fields, and a direct unit test on `PublicReadOnly`

### Closed out
Full test suite green, no migrations needed (federation has no models of its own). Section done — per the build order, §10 (acceptance test) can now run its first pass; §07 (bundled UI) is next after that.
