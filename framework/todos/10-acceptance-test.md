# TODO 10 — Acceptance Test (the seven steps)

> Status: not started
> Blueprint: [§10](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Minimal Working Community"
> Depends on: 02, 03, 04, 05, 06 · Blocks: seed release
> Runs early (as soon as §06 exists) and re-runs after every section.

## Goal
The end-to-end gate. When these seven steps pass on a fresh SQLite install with zero frontend work, the seed model is proven.

## Tasks
- [ ] `tests/test_acceptance.py` scripting the seven steps:
  1. `betat init` + declare standard (≥ baseline)
  2. Provenancier enrolls via a protocol-list method
  3. submit a text contribution (content elsewhere, hash provided)
  4. verifier reviews + accepts
  5. valid PROVENANCE_SPEC v0.1 record with `hi_tag:true` + declared standard in store
  6. `/betat/records` returns it; `verify_integrity` passes; no path modifies/deletes it
  7. an independent crawler, given only the host address, discovers + reads it

## Acceptance criteria
- [ ] all seven pass on a fresh SQLite install
- [ ] zero frontend work required to pass
- [ ] the test is the CI gate for a seed release

## Security notes
- Step 6 must assert the absence of any update/delete path, not just that none was called

## Out of scope
- UI polish (§07/§08) — acceptance runs headless via the API
