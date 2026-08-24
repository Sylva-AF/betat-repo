# TODO 08 — Post-Install Seed Website

> Status: in progress — everything buildable is done and tested (green on both engines); the one open item ("items deep-link to docs") is blocked on §11, not on this section
> Blueprint: [§8](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "The post-install seed website"
> Depends on: 02, 07 · Blocks: nothing

## Goal
A Django-style first-run page that proves the install works and shows the readiness checklist — the honest distance between "it runs" and "it is production-ready."

## Tasks
- [x] First-run landing page (in bundledui)
- [x] Readiness checklist, four items: robust DB engine (PostgreSQL) · provenance assertions/records · authentication method · UI bundle
- [x] Each item links its docs page and shows outstanding/done from real config state
- [x] State reflects actual configuration, not a static list

## Acceptance criteria
- [x] fresh install shows the page with correct outstanding states
- [ ] items deep-link to docs — **blocked on §11**: links to `https://betat.org` as an honest placeholder (`DOCS_PLACEHOLDER` in `views.py`) since there are no real per-item docs pages to link to yet. Not closeable by more work in this section.
- [x] completing a step flips its state — derived live from `connection.vendor` + `/betat/info`, not a static list

## Security notes
- The page must not expose config secrets or internal paths

## Out of scope
- Writing the docs pages themselves (§11)

## Session handoff

### Design decisions (full rationale in BLUEPRINT §08 Decision Log)
- **This page is not bound by §07's "public API only" rule the same way.** It's an operator/ops status view, not part of the Layer 2 consumption model — checking `connection.vendor` directly for the DB-engine item is correct here, since that's infrastructure state that has no business being exposed on any public API. The "is this install configured" check still goes through `ApiClient`/`/betat/info`, since that part genuinely is API-shaped.
- **Doc links are a placeholder (`https://betat.org`), not real per-item deep links** — §11 (docs site) doesn't exist yet, so there's nowhere real to link to. Marked with a `DOCS_PLACEHOLDER` constant in `views.py` so it's easy to find and replace once §11 ships real pages.
- **Only two of the four checklist items are actually distinguishable by current config state** — "provenance records" and "auth method" both resolve to the same underlying fact (`CommunityConfig` exists with a non-empty `auth_methods`, since our model doesn't support partial/staged configuration) and so always move together. The "UI bundle" item is always `DONE` (the bundled UI ships by definition — there's no partial-install state for it). This isn't a shortcut, it's an honest reflection of what the codebase can actually distinguish; not inventing fake granularity.
- **Root path `/` now belongs to this page** — `betat_community/urls.py` mounts it directly, separate from `/community/` (§07's prefix).

### Files written this section
- `bundledui/views.py` — `landing_view`, `DOCS_PLACEHOLDER`
- `bundledui/templates/bundledui/landing.html`
- `betat_community/urls.py` — mounts `/` → `landing_view`
- `tests/test_bundledui.py` — two new tests (not-configured state, configured state)

### Closed out
Full suite green on both SQLite (79/79) and PostgreSQL (77 passed + 2 expected skips). Confirmed in a browser at `/`. Stays `in progress` (not `done`) purely because of the doc-links gap above — revisit once §11 exists and swap `DOCS_PLACEHOLDER` for real per-item links.
