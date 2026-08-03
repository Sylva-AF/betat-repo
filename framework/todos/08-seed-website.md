# TODO 08 — Post-Install Seed Website

> Status: not started
> Blueprint: [§8](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "The post-install seed website"
> Depends on: 02, 07 · Blocks: nothing

## Goal
A Django-style first-run page that proves the install works and shows the readiness checklist — the honest distance between "it runs" and "it is production-ready."

## Tasks
- [ ] First-run landing page (in bundledui or core)
- [ ] Readiness checklist, four items: robust DB engine (PostgreSQL) · provenance assertions/records · authentication method · UI bundle
- [ ] Each item links its docs page and shows outstanding/done from real config state
- [ ] State reflects actual configuration, not a static list

## Acceptance criteria
- [ ] fresh install shows the page with correct outstanding states
- [ ] items deep-link to docs
- [ ] completing a step flips its state

## Security notes
- The page must not expose config secrets or internal paths

## Out of scope
- Writing the docs pages themselves (§11)
