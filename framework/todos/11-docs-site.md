# TODO 11 — Documentation Site

> Status: in progress — content complete locally; **not yet live** — the new files have never actually been pushed (see "Still to do", this is the very next thing to fix)
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
- **New pages nest under the existing "For Builders" section — flat, not three-level.** First attempt used Just the Docs' `parent`/`grand_parent`/`has_children` three-level nav (`framework-reference.md` as an intermediate hub with children). Changed to flat `parent: For Builders` directly (`nav_order` 5–8) — the exact same pattern ARCHITECTURE.md/COMMUNITY_FRAMEWORK.md/PROVENANCE_SPEC.md/RENDERING.md already use successfully on this site. **Important correction:** this was originally diagnosed as "the fix" for a live 404 on `betat.org/framework-cli.html`, but the real root cause (found later, see "Still to do") is that the pages were never actually pushed at all — so the three-level nesting theory was never actually tested live and might have worked fine. Kept the flatten anyway since it matches the proven pattern and there's no reason to prefer the untested approach, but don't repeat "three-level nav is broken on this site" as a confirmed fact — it isn't confirmed.
- **URLs weren't guessed** — Jekyll's default permalink style (`<name>.html` at site root) was confirmed directly from `index.md`'s own existing internal links (e.g. `for-builders.html`) before writing any cross-references, so `https://betat.org/framework-cli.html` etc. are real, not fabricated.
- **§08's readiness checklist now links to real pages** — `bundledui/views.py`'s `DOCS_PLACEHOLDER` is gone, replaced with `DOCS_CLI`/`DOCS_API` pointing at the actual new pages. §08 moves to `done` as a result (see its own file).
- **"Definition of done includes docs" landed as a new Ground Rule in `CONTRIBUTING.md`**, not a separate PR template file (none existed; adding the rule to the existing Ground Rules list is the smaller, more consistent change).

### Files written this section
- `framework-reference.md`, `framework-cli.md`, `framework-api.md`, `framework-store.md` — new, at repo root. Content is final: CLI/API/store snippets, plus a "running locally?" note at the top of `framework-api.md` explaining the `https://your-community.example` → `http://127.0.0.1:8000` substitution for dev use.
- `CONTRIBUTING.md` — new Ground Rule ("Definition of done includes docs")
- `betat_community/bundledui/views.py` — `DOCS_PLACEHOLDER` → `DOCS_CLI`/`DOCS_API`
- `tests/test_bundledui.py` — one new test confirming the real links render (passing, part of the 95/95 green run)

### THE ROOT CAUSE of the live 404 (read this before doing anything else)
Every git session this TODO was worked in ran from inside `framework/` (shell prompt `[user@host framework]$`), and `git add .` / `git commit` from a subdirectory only stages files **within that subdirectory**. The four new `.md` pages and the `CONTRIBUTING.md` edit all live at the **actual repo root**, one level above `framework/` — so across two separate commits ("Add documentation pages for the framework" and "Documentation pages bug fixed"), **neither ever actually included them**. Both commits only touched files already under `framework/` (`BLUEPRINT.md`, `TODO.md`, `todos/*.md`, `betat_community/bundledui/views.py`, `tests/test_bundledui.py`). Confirmed via `git show --stat HEAD` mid-session. This is why the live site 404s — it isn't a Jekyll/front-matter bug, the content has simply never been pushed.

### Still to do (developer actions) — do these in order
1. **From the repo root** (run `pwd`, confirm it does NOT end in `/framework` before proceeding):
   ```bash
   git status   # should list framework-cli.md, framework-api.md, framework-store.md,
                # framework-reference.md, and CONTRIBUTING.md — WITHOUT a "../" prefix
   git add framework-cli.md framework-api.md framework-store.md framework-reference.md CONTRIBUTING.md
   git commit -m "Add the actual framework docs pages (previous commits missed these)"
   git push
   ```
2. Wait a minute or two for GitHub Pages to rebuild, then check `betat.org/framework-cli.html` (and `-api`, `-store`, `-reference`) actually resolve — this will be the **first real test** of both the page content and the flat-nav front matter, since nothing has been live before now.
3. `pytest tests/` from `framework/` — already green (95/95) as of the last run; nothing in this outstanding fix touches test-covered code, so no regression expected, but worth a fresh run anyway since it's cheap.
4. Once the live site confirms: flip `TODO.md`'s status to `done`. §08 was marked `done` on the assumption these links would resolve — re-check that once the site is actually live, since it was marked before any of this was discovered.
