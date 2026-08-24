# TODO 11 — Documentation Site

> Status: in progress — content complete, awaiting developer confirmation (Jekyll build + tests) — see "Session handoff"
> Blueprint: [§11](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Documentation Standard"
> Depends on: 01-09 (documents what they built) · Blocks: nothing

## Goal
A readthedocs-style site where every public capability has a copyable snippet with real output — so the whole framework is learnable by reading top-to-bottom and running examples.

## Tasks
- [x] Docs site scaffold (readthedocs-style) — reuses the existing public Jekyll site, not a new toolchain (see handoff — this reverses this file's original "out of scope" line)
- [x] A snippet per: every API endpoint, every framework function, every CLI command — call, inputs, real output
- [x] Readiness-checklist items (§08) deep-link into these pages
- [x] State the PR rule: public behavior change must update its docs page

## Acceptance criteria
- [x] every §1-§9 public capability has a runnable snippet
- [x] checklist links resolve into the docs
- [x] "definition of done includes docs" is enforced in CONTRIBUTING/PR template

## Security notes
- Example snippets use placeholder secrets/tokens only, never real ones

## Out of scope
- ~~The public Jekyll site at betat.org~~ — **reversed**: the Jekyll site *is* where this section's docs live now (zero-budget hosting decision, see handoff)

## Session handoff

### Design decisions (full rationale in BLUEPRINT §11 Decision Log)
- **Reused the existing public Jekyll site instead of a new docs toolchain (MkDocs/Sphinx/ReadTheDocs.io).** Explicit developer call: Betat runs on zero budget, and the Jekyll/GitHub Pages site is already live and free. This reverses this file's original "out of scope" line, which assumed a separate framework-specific doc system. `_config.yml` excludes `framework/` from the Jekyll build, so the new pages live at the **repo root**, not `framework/docs/` — Jekyll would silently ignore anything placed there.
- **New pages nest under the existing "For Builders" section — flat, not three-level.** First attempt used Just the Docs' `parent`/`grand_parent`/`has_children` three-level nav (`framework-reference.md` as an intermediate hub with children). After committing and pushing, `betat.org/framework-cli.html` 404'd — the three-level nesting likely isn't supported by whatever Just the Docs version GitHub Pages actually resolves for this remote-theme setup (unconfirmed root cause, not chased further). **Fixed** by flattening all four pages to `parent: For Builders` directly, `nav_order` 5–8 — the exact same flat pattern ARCHITECTURE.md/COMMUNITY_FRAMEWORK.md/PROVENANCE_SPEC.md/RENDERING.md already use and which is proven to work live on this site. Titles also simplified to match ("Framework CLI" rather than "CLI Commands", etc.) — cosmetic, not part of the fix.
- **URLs weren't guessed** — Jekyll's default permalink style (`<name>.html` at site root) was confirmed directly from `index.md`'s own existing internal links (e.g. `for-builders.html`) before writing any cross-references, so `https://betat.org/framework-cli.html` etc. are real, not fabricated.
- **§08's readiness checklist now links to real pages** — `bundledui/views.py`'s `DOCS_PLACEHOLDER` is gone, replaced with `DOCS_CLI`/`DOCS_API` pointing at the actual new pages. §08 moves to `done` as a result (see its own file).
- **"Definition of done includes docs" landed as a new Ground Rule in `CONTRIBUTING.md`**, not a separate PR template file (none existed; adding the rule to the existing Ground Rules list is the smaller, more consistent change).

### Files written this section
- `framework-reference.md`, `framework-cli.md`, `framework-api.md`, `framework-store.md` — new, at repo root
- `CONTRIBUTING.md` — new Ground Rule ("Definition of done includes docs")
- `betat_community/bundledui/views.py` — `DOCS_PLACEHOLDER` → `DOCS_CLI`/`DOCS_API`
- `tests/test_bundledui.py` — one new test confirming the real links render

### Still to do (developer actions)
1. Commit + push the front-matter fix (flattened nav), then re-check `betat.org/framework-cli.html` (and `-api`, `-store`, `-reference`) actually resolve — the previous attempt 404'd before this fix.
2. `pytest tests/` — already green (95/95) as of the last run, unaffected by this front-matter-only change.
3. Once the live site confirms: flip `TODO.md`'s status to `done`. §08 was marked `done` on the assumption these links would resolve — worth a quick re-check there too once the site is live, since it was marked before this bug was found.
