# TODO 11 — Documentation Site

> Status: not started
> Blueprint: [§11](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Documentation Standard"
> Depends on: 01-09 (documents what they built) · Blocks: nothing

## Goal
A readthedocs-style site where every public capability has a copyable snippet with real output — so the whole framework is learnable by reading top-to-bottom and running examples.

## Tasks
- [ ] Docs site scaffold (readthedocs-style)
- [ ] A snippet per: every API endpoint, every framework function, every CLI command — call, inputs, real output
- [ ] Readiness-checklist items (§08) deep-link into these pages
- [ ] State the PR rule: public behavior change must update its docs page

## Acceptance criteria
- [ ] every §1-§9 public capability has a runnable snippet
- [ ] checklist links resolve into the docs
- [ ] "definition of done includes docs" is enforced in CONTRIBUTING/PR template

## Security notes
- Example snippets use placeholder secrets/tokens only, never real ones

## Out of scope
- The public Jekyll site at betat.org (that is the repo-root docs, not the framework docs)
