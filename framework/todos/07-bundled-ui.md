# TODO 07 — Bundled Minimal UI

> Status: not started
> Blueprint: [§7](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Consumption Model, Layer 2" · [RENDERING.md](../RENDERING.md)
> Depends on: 03, 04, 06 · Blocks: 08

## Goal
The `bundledui` app: a plain, server-rendered UI so a fresh install is usable with zero frontend work — enroll, submit, review queue, public records list + detail — consuming the public API only.

## Tasks
- [ ] Django templates (no build step, no Node): enroll, submit, review-queue, records-list, record-detail
- [ ] All data via the public JSON API — no ORM shortcuts
- [ ] Render per RENDERING.md card + evidence views
- [ ] Integrity states (BINDING): validate `record_id` → tampered state; content-hash → verified / changed / unreachable; always show declared standard beside HI badge; always link full record; absence → unverified (never "fake")

## Acceptance criteria
- [ ] four views work on a fresh install, zero frontend work
- [ ] each view's data comes through the API (provable)
- [ ] tampered / changed / unreachable fixtures each render the correct state
- [ ] evidence ("view full record") link resolves to raw JSON

## Security notes
- No credentials or tokens rendered into templates or logs
- A detected mismatch must never render as a normal card

## Out of scope
- The first-run readiness page (§08)
- Any non-bundled frontend (Layer 3, community's own)
