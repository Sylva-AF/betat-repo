# TODO 06 — Federation Endpoints

> Status: not started
> Blueprint: [§6](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Federation endpoints"
> Depends on: 02, 05 · Blocks: 07, 10

## Goal
The `federation` app: the community's public face — four read-only JSON endpoints any registry, crawler, or index can call without authentication.

## Tasks
- [ ] `GET /betat/info` → `CommunityConfig` (identity + declared standard)
- [ ] `GET /betat/records` → paginated, newest-first; `?hi_only=` filter
- [ ] `GET /betat/records/{id}` → one record
- [ ] `GET /betat/changes?since=` → records after a timestamp (incremental crawl)
- [ ] DRF serializers exposing exactly the record schema — no internal fields leak
- [ ] Pagination + consistent ordering

## Acceptance criteria
- [ ] all four return valid JSON, unauthenticated
- [ ] a written record appears at `/records` and `/records/{id}`
- [ ] `since=` filters correctly
- [ ] no endpoint requires auth
- [ ] acceptance-test step 7 (independent crawler, host address only) passes

## Security notes
- Read-only: no POST/PUT/DELETE on this surface
- Serializers must not expose internal DB ids or non-spec fields

## Out of scope
- Writing records (§04)
- Crawling (never in this package — index operators crawl)
