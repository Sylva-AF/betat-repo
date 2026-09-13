# Betat Community Framework — Build Plan

> Development tracker for the seed implementation of [COMMUNITY_FRAMEWORK.md](../COMMUNITY_FRAMEWORK.md) v0.2.
> One TODO file per framework section. The structure below is maintained throughout development,
> though the final product ships as a single package: `betat-community`.
> Each TODO is written to be handed directly to a development session (Claude Code or human).

| # | Section | TODO file | Spec reference | Status |
|---|---------|-----------|----------------|--------|
| 01 | Project scaffold & CLI | [todos/01-scaffold-cli.md](todos/01-scaffold-cli.md) | What an Operator Gets | done |
| 02 | Config & community identity | [todos/02-config-identity.md](todos/02-config-identity.md) | Community Identity; CommunityConfig | done |
| 03 | Authentication plugins & floor | [todos/03-authentication.md](todos/03-authentication.md) | Authentication (pluggable, floored) | done |
| 04 | Submission & verification workflow | [todos/04-workflow.md](todos/04-workflow.md) | Submission and verification workflow | done |
| 05 | Append-only provenance store | [todos/05-provenance-store.md](todos/05-provenance-store.md) | Append-only store; PROVENANCE_SPEC | done |
| 06 | Federation endpoints | [todos/06-federation.md](todos/06-federation.md) | Federation endpoints | done |
| 07 | Bundled minimal UI | [todos/07-bundled-ui.md](todos/07-bundled-ui.md) | Consumption Model, Layer 2 | done |
| 08 | Post-install seed website | [todos/08-seed-website.md](todos/08-seed-website.md) | The post-install seed website | done |
| 09 | Discoverability: announce & export | [todos/09-discoverability.md](todos/09-discoverability.md) | announce / export | done |
| 10 | Acceptance test (the 7 steps) | [todos/10-acceptance-test.md](todos/10-acceptance-test.md) | Minimal Working Community | done |
| 11 | Documentation site | [todos/11-docs-site.md](todos/11-docs-site.md) | Documentation Standard | in progress |
| 12 | Packaging & production guide | [todos/12-packaging.md](todos/12-packaging.md) | Design Goal 4; storage engines | in progress |
| 13 | Operator & Provenancier UX — admin dashboard, adaptive access | [todos/13-operator-provenancier-ux.md](todos/13-operator-provenancier-ux.md) | Consumption Model, Layer 2; Authentication (pluggable, floored) | done |

Build order: 01 → 02 → 05 → 03 → 04 → 06 → 10 (first acceptance pass) → 07 → 08 → 09 → 11 → 12.
The store (05) comes early because everything writes to it; the acceptance test (10) runs as soon as
the API path exists, then re-runs after every section.

**13 gated the v0.1 ship — cleared 2026-09-13.** Opened 2026-09-12 from real usability gaps found
during TODO 12's fresh-venv verification walkthrough (Django-admin-only enrollment approval, a
passphrase login form that can never work for peer-vouch/institutional identities, no way to verify
a mistyped passphrase before submitting). All six resulting tasks are now done and test-confirmed;
see its own file for full context and BLUEPRINT §03/§07's 2026-09-12/13 Decision Log entries for
implementation detail. With 13 clear, TODO 11 (docs site — pending push from repo root) and TODO 12
(packaging — `settings_production.py` retirement done 2026-09-13; wheel rebuild, fresh-venv verify,
dual-DB Postgres gate, and a production-guide dry run remain, all developer-run) are the only
sections left before v0.1 can ship.

**Status values:** not started · in progress · blocked · done (all acceptance criteria pass).
Update the status column in the same commit that changes the work.
