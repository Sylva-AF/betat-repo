# TODO 08 — Post-Install Seed Website

> Status: done — §11 shipped real docs pages; the checklist now links to them (see "Closed out")
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
- [x] items deep-link to docs — `betat.org/framework-cli.html` and `.../framework-api.html` (§11), real and resolving
- [x] completing a step flips its state — derived live from `connection.vendor` + `/betat/info`, not a static list

## Security notes
- The page must not expose config secrets or internal paths

## Out of scope
- Writing the docs pages themselves (§11)

## Session handoff

### Design decisions (full rationale in BLUEPRINT §08 Decision Log)
- **This page is not bound by §07's "public API only" rule the same way.** It's an operator/ops status view, not part of the Layer 2 consumption model — checking `connection.vendor` directly for the DB-engine item is correct here, since that's infrastructure state that has no business being exposed on any public API. The "is this install configured" check still goes through `ApiClient`/`/betat/info`, since that part genuinely is API-shaped.
- **Doc links originally pointed at a placeholder** (`DOCS_PLACEHOLDER = 'https://betat.org'`) since §11 didn't exist yet. **Update (§11 session):** replaced with real, resolving links — `DOCS_CLI`/`DOCS_API` constants pointing at the new Framework Reference pages on the public Jekyll site (`betat.org/framework-cli.html`, `.../framework-api.html`).
- **Only two of the four checklist items are actually distinguishable by current config state** — "provenance records" and "auth method" both resolve to the same underlying fact (`CommunityConfig` exists with a non-empty `auth_methods`, since our model doesn't support partial/staged configuration) and so always move together. The "UI bundle" item is always `DONE` (the bundled UI ships by definition — there's no partial-install state for it). This isn't a shortcut, it's an honest reflection of what the codebase can actually distinguish; not inventing fake granularity.
- **Root path `/` now belongs to this page** — `betat_community/urls.py` mounts it directly, separate from `/community/` (§07's prefix).

### Files written this section
- `bundledui/views.py` — `landing_view`, `DOCS_CLI`/`DOCS_API` (updated in the §11 session; were `DOCS_PLACEHOLDER`)
- `bundledui/templates/bundledui/landing.html`
- `betat_community/urls.py` — mounts `/` → `landing_view`
- `tests/test_bundledui.py` — landing-page tests, plus one added in the §11 session confirming the real doc links render

### Closed out
Full suite green on both SQLite and PostgreSQL. Confirmed in a browser at `/`. The doc-links gap is now closed — §11 shipped real pages and this section's checklist links to them. Section done.
