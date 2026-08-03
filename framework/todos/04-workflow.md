# TODO 04 — Submission & Verification Workflow

> Status: not started
> Blueprint: [§4](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Submission and verification workflow"
> Depends on: 02, 03, 05 · Blocks: 06, 10

## Goal
The `workflow` app: an authenticated Provenancier submits a content reference; a verifier reviews; acceptance builds a valid record and appends it to the store.

## Tasks
- [ ] `Submission` model: content_ref (URI/DOI/IPFS) + content_hash, identity, declaration, status
- [ ] `/betat/submit` — requires authenticated identity; content is NEVER uploaded, only ref + hash
- [ ] `/betat/queue` — verifier-only pending list
- [ ] `/betat/review/{id}` — accept | reject; records verifier identity + timestamp
- [ ] `build_record()`: PROVENANCE_SPEC v0.1; declared standard → `declaration.custom_addition`; `hi_tag=true`
- [ ] accept → `store.append()`; reject → close submission, no record

## Acceptance criteria
- [ ] unauthenticated submit refused
- [ ] accept yields a spec-valid record in the store; reject yields none
- [ ] verifier identity + timestamp present in the record
- [ ] `authentication_method` from §03 present in the record

## Security notes
- Enforce identity.is_authenticated at submit — no anonymous path
- `content_hash` is taken as given at submit (the source of truth for later integrity checks); never recomputed from uploaded content because content is never uploaded

## Out of scope
- Hashing/append mechanics (§05) — workflow calls the store, doesn't reimplement it
- Serving records (§06)
