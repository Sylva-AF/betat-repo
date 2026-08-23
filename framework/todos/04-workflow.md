# TODO 04 — Submission & Verification Workflow

> Status: done — all acceptance criteria pass (migrations applied, full test suite green)
> Blueprint: [§4](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Submission and verification workflow"
> Depends on: 02, 03, 05 · Blocks: 06, 10

## Goal
The `workflow` app: an authenticated Provenancier submits a content reference; a verifier reviews; acceptance builds a valid record and appends it to the store.

## Tasks
- [x] `Submission` model: location (URI/DOI/IPFS) + content_hash, provenancier FK, declaration_accepted, status
- [x] `/betat/submit` — requires authenticated identity; content is NEVER uploaded, only ref + hash
- [x] `/betat/queue` — verifier-only pending list
- [x] `/betat/review/{id}` — accept | reject; records verifier identity + timestamp
- [x] `build_record()`: PROVENANCE_SPEC v0.1; declared standard → `declaration.custom_addition`; `hi_tag=true`
- [x] accept → `store.append()`; reject → close submission, no record

## Acceptance criteria
- [x] unauthenticated submit refused (401)
- [x] accept yields a spec-valid record in the store; reject yields none
- [x] verifier identity + timestamp present in the record
- [x] `authentication_method` from §03 present in the record

## Security notes
- Enforce identity.is_authenticated at submit — no anonymous path
- `content_hash` is taken as given at submit (the source of truth for later integrity checks); never recomputed from uploaded content because content is never uploaded

## Out of scope
- Hashing/append mechanics (§05) — workflow calls the store, doesn't reimplement it
- Serving records (§06)

## Session handoff

### Design decisions (logged in BLUEPRINT.md §04 Decision Log — read there for full rationale)
- **"Verifier" = Django staff user** (`is_staff=True`), not a new identity model. Managed via the admin panel. `workflow/api/mixins.py`'s `IsVerifier` checks `request.user.is_staff`; `verified_by` = the staff account's `username`.
- **`verification.method` fixed to `'editorial_review'`** — the only verification method this framework's actual review flow matches.
- **`content_type` is not a submit-time input** — `build_record()` always reads `CommunityConfig.content_type`; a community verifies exactly one type.
- **`declaration_accepted` must be exactly `true` at submit** — refused (400) otherwise, not deferred to review.

### Files written this section
- `workflow/models.py` — `Submission`
- `workflow/record_builder.py` — `build_record()`, `DECLARATION_TEXT`, `VERIFICATION_METHOD`
- `workflow/api/mixins.py` — `IsVerifier` permission
- `workflow/api/serializers.py` — `SubmitRequestSerializer`, `ReviewRequestSerializer`, `SubmissionSerializer`
- `workflow/api/views.py` — `SubmitView`, `QueueView`, `ReviewView`
- `betat_community/urls.py` — mounts `/betat/submit`, `/betat/queue`, `/betat/review/<int:submission_id>`
- `framework/tests/test_workflow.py` — new, 11 tests covering every acceptance criterion above plus queue filtering, already-reviewed conflict, and invalid-decision rejection

### Closed out
Developer applied `makemigrations workflow` + `migrate`, fixed a mangled docstring in `record_builder.py` (stray code fragments had landed inside the module docstring text), added `record_signature: ''` to `build_record()`'s output (present-but-empty pending real signing support), and added `CommunityConfig.DoesNotExist` handling in `ReviewView` (503 `not_configured`, matching `EnrollView`'s existing pattern) — `MultipleObjectsReturned` deliberately left uncaught, see the inline comment in `views.py`. Full test suite green. Section done — next up is §06 (federation endpoints), which serves what §04/§05 write; §10 (acceptance test) can also start once §06 exists per the build order.
