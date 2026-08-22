# TODO 12 — Packaging & Production Guide

> Status: not started
> Blueprint: [§12](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Design Goal 4", "storage engines"
> Depends on: 01-10 · Blocks: seed release

## Goal
Ship the single installable package, and document the honest path from SQLite (evaluation) to PostgreSQL (production) — where append-only becomes a database-permission guarantee, not just triggers + code.

## Tasks
- [ ] Finalize `pyproject.toml`; build + verify a wheel/sdist
- [ ] `pip install` from the built artifact works clean (not just `-e`)
- [ ] "Recommended production stack" guide: PostgreSQL install, config, and role setup — app role INSERT/SELECT only, UPDATE/DELETE revoked
- [ ] SQLite → PostgreSQL migration route, documented + tested
- [ ] Document Python 3.11 floor, tested through 3.12+

## Acceptance criteria
- [ ] clean install from built artifact works
- [ ] SHIP GATE: acceptance suite (TODO 10) and store suite (TODO 05) pass on BOTH SQLite and PostgreSQL — this is the founder's dual-DB verification before shipping
- [ ] the ONLY production step documented for end users is: point database settings at PostgreSQL and deploy (no code changes, no Postgres wrestling at production time)
- [ ] production guide runs end-to-end
- [ ] on PostgreSQL, raw UPDATE/DELETE by the app role fails at the DB-permission level

## Security notes
- The production guide's role revocation is the REAL append-only boundary — emphasize it over the SQLite triggers, and never claim SQLite matches it
- Secret-key and DB-credential handling documented via env vars, never committed

## Out of scope
- New features — this section hardens and ships what §1-§10 built
