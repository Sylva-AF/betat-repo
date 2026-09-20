# TODO 15 — Absolute content-URL enforcement + login-page readability

> Status: done — pytest green and manual check signed off by the developer.
> Blueprint: no dedicated section — landed as a Decision Log entry under §04/§07 (2026-09-20).
> Spec reference: PROVENANCE_SPEC.md (content `location`); COMMUNITY_FRAMEWORK.md "Consumption Model, Layer 2".
> Depends on: 04, 07.

## Why this exists

Two issues found reviewing the shipped UI after an accept:

1. **A record's "Source ↗" link resolved to the community's own host.** The link is
   `href="{{ record.content.location }}"` (the raw submitted value). A bare `bantu.org` (no
   scheme) is a *relative* URL, so it resolved to `http://localhost:8000/community/records/bantu.org`
   — and in production would resolve relative to the community domain, still wrong. It should point
   straight at the external content (Betat stores provenance, not content).
2. **The verifier sign-in CTA on the login page was near-invisible** — muted 13px text on the gray
   body. (Developer chose "fix contrast in place", keeping the card-on-gray design, over a white
   content panel.)

## Tasks

- [x] **Enforce an absolute content location at submit.** New `betat_community/common/validators.py`
  `validate_content_location` — allowlisted schemes (`http`, `https`, `ftp`, `ipfs`, `ipns`, `doi`)
  with an address after the scheme; rejects bare/relative values and unsafe `javascript:`/`data:`
  (latent stored-XSS on the Source href). Wired into `SubmitRequestSerializer.location`
  (authoritative — bundledui posts through it) and `SubmitForm.location` (inline UI feedback).
  `build_record()` unchanged (validation at ingress). **Append-only:** guards future submissions
  only; existing bare-`location` records can't be edited — a correction is a new record.
- [x] **Login CTA readability.** `provenancier_login.html`: the verifier sign-in line is now an
  ink-colored lead sentence + a `bt-btn-secondary bt-btn-sm` link, visible on the gray body.

## Acceptance criteria

- [x] `POST /betat/submit` with a scheme-less `location` (e.g. `bantu.org`) returns 400 and writes
  no `Submission`; an absolute `https://…`/`ipfs://…`/`doi:…` succeeds. *(pytest confirmed)*
- [x] The bundled submit form re-renders with a validation error (no redirect, no `Submission`) for
  a bare location. *(pytest confirmed)*
- [x] The verifier sign-in CTA on `/community/login` renders as a visible button-style link. *(manual — signed off)*

## Out of scope

- Rewriting/repairing already-accepted records with bad locations (append-only store).
- Any change to the review/accept flow itself (staff-verifier acceptance is the intended seed flow
  — BLUEPRINT §04, `editorial_review`).
- A white content-panel restyle of the app (developer chose contrast-in-place).

## Verification (developer-run — sandbox blocks Bash here)

1. `pytest tests/test_workflow.py tests/test_bundledui.py`
2. Manual: submit with a bare domain → see the rejection; submit `https://…` → accept → the record
   card's "Source ↗" opens the external URL; check the login page's verifier CTA is clearly visible.
