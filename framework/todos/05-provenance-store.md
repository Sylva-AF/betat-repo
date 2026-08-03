# TODO 05 — Append-Only Provenance Store

> Status: not started
> Spec: COMMUNITY_FRAMEWORK.md → "Append-only store" · PROVENANCE_SPEC.md (record format, hashing, corrections)
> Depends on: 01 (scaffold), 02 (config/identity)
> Blocks: 03, 04, 06, 10

## Goal

The permanent record layer: a store that accepts valid PROVENANCE_SPEC v0.1 records, preserves them append-only, serves them back, and can prove their integrity. When this section is done, a record written today is readable, verifiable, and unmodifiable by any code path in the package.

## Tasks

- [ ] Django model for `ProvenanceRecord` mirroring PROVENANCE_SPEC v0.1 fields exactly (field names are spec-permanent: `hi_tag`, `provenancier`, etc.)
- [ ] Canonicalization function: record JSON with `record_id` and `record_signature` set to `""`, keys sorted alphabetically, no whitespace (per spec Implementation Notes)
- [ ] `record_id` = SHA-256 of canonical form; computed at append, never accepted from the caller
- [ ] `append(record)` — validates against spec (reject if `hi_tag` is not `true`; reject missing required fields), computes hash, inserts
- [ ] `get(record_id)` / `list(since, page)` — pagination newest-first
- [ ] `verify_integrity(record_id)` — recompute hash, compare, return boolean
- [ ] `correction_of` / `disputes` reference fields accepted as new records only
- [ ] SQLite guard triggers: `BEFORE UPDATE` and `BEFORE DELETE` on the records table → `RAISE(ABORT)` — installed by migration
- [ ] No `update()` / `delete()` methods anywhere in the store class — deliberate absence, enforced by test
- [ ] PostgreSQL notes stub for TODO 12: role grant script (INSERT/SELECT only; UPDATE/DELETE revoked)

## Acceptance criteria

- [ ] A spec-valid record appends and reads back byte-identical
- [ ] `verify_integrity` passes on clean records; fails after any manual byte tampering in a test
- [ ] A record with `hi_tag: false` or missing is rejected
- [ ] Raw SQL `UPDATE`/`DELETE` against the table fails on SQLite (trigger) — test proves it
- [ ] Acceptance test steps 5 and 6 (store half) pass

## Security notes

- The hash is computed server-side, always — a caller-supplied `record_id` is an attack surface
- Canonicalization must be deterministic across Python versions (use `json.dumps(..., sort_keys=True, separators=(",",":"))`)
- Triggers are defense-in-depth, not the security boundary; the spec's honest position (app-level + triggers on SQLite, role revocation on PostgreSQL) is documented in COMMUNITY_FRAMEWORK.md and must not be overstated in docs

## Out of scope for this section

- Federation endpoints (06) — the store is storage, not transport
- Record building from submissions (04) — the store validates and keeps; it does not compose
- PostgreSQL setup itself (12) — only the grant-script stub lands here
