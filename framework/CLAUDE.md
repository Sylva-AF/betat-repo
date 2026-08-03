# CLAUDE.md — Session Bootstrap for the Betat Community Framework

You are working on the **Betat community framework** — the reference implementation of [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md). Read this file first, every session.

## Read in this order before writing code

1. **[BLUEPRINT.md §0](BLUEPRINT.md)** — the whole picture: locked decisions, the tree, the API table, data flow, conventions. Always.
2. **BLUEPRINT.md §NN** — the section matching the work unit you were given.
3. **[todos/NN](todos/)** — the task checklist and acceptance criteria for that section.
4. The spec section each of the above references, if you need the source of truth.

## Authority hierarchy (resolve conflicts upward)

**spec → blueprint → TODOs → code.** The higher document wins. If code needs to diverge from the blueprint, add a **Decision Log** entry in BLUEPRINT.md *first*, then write the code, in the same commit. Never silently code around the blueprint.

## The locked decisions (do not relitigate mid-session)

venv + pip · Django REST Framework · thin `betat` CLI over management commands · six apps nested in `betat_community/` · Python 3.11 floor · pytest + pytest-django. If one genuinely blocks the work, stop and raise it as a Decision Log question — don't quietly substitute another.

## Guardrails (hard rules)

- **Spec-permanent names never change:** `hi_tag`, `provenancier`, and PROVENANCE_SPEC field names are fixed.
- **The store has no update/delete path** — not in code, not in the API, ever. Corrections/disputes are new records.
- **Reading endpoints are public and unauthenticated** — always. Never add auth to a GET in the API table.
- **Content is never uploaded** — only `content_ref` + `content_hash`. The framework stores provenance, not content.
- **The bundled UI consumes the public API only** — no ORM shortcuts; its integrity-state rendering (RENDERING.md) is binding.
- **Out-of-scope means stop.** Each TODO lists what belongs to other sections. Do not build across the boundary; open the next section's work unit instead.
- **Definition of done includes a doc snippet** for any public capability.

## Workflow

- One branch per section: `feat/NN-<slug>` (e.g. `feat/05-provenance-store`), branched from fresh `main`.
- Every acceptance-criterion line maps to at least one pytest test.
- Update the section's status in [TODO.md](TODO.md) in the same commit that completes it.
- Commit messages name the section: `Store: append-only model with canonical hashing (TODO 05)`.

## What to do when unsure

Prefer the boring, documented choice already in the blueprint. If the blueprint is silent, ask rather than invent — an unrecorded structural decision is the thing most likely to desync sections. Security and record-integrity over elegance, always.

---

*Detail: [BLUEPRINT.md](BLUEPRINT.md) · Plan: [TODO.md](TODO.md) · Spec: [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md)*
