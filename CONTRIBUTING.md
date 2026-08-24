---
title: Contributing
parent: The Project
nav_order: 1
---

# Contributing to Betat

Thank you for considering a contribution. Betat is a seed — every improvement, however small, is a human act in a project about human acts.

---

## First: Which Role Are You In?

Betat distinguishes two roles. Read this before anything else:

**Contributor** — a developer or technologist who builds, improves, or extends the Betat open-source codebase. Contributors participate here, on GitHub, through issues and pull requests. **This document is for you.**

**Provenancier** *(pro-VEN-an-see-ay)* — a verified human being who records, archives, or submits human-originated content to a Betat community. Provenanciers do not participate through this repository — they participate through communities. If you want to record human content rather than build software, start with [README.md](README.md) and find (or seed) a community in your domain.

The same person may hold both roles, but the roles are always described separately.

---

## What to Work On

The current build priorities are defined in [ARCHITECTURE.md](ARCHITECTURE.md) under **What To Build First**:

1. The community framework reference implementation (see [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md))
2. The registry — a small app implementing the registry interface
3. A reference crawler + index — reads the registry, crawls federation endpoints, serves search with `hi_only`
4. A browser extension — the first tag-on-render client
5. Improvements to the protocols and these documents

If something in the documents is unclear, underspecified, or wrong — that is a contribution too. Open an issue or submit a pull request.

---

## How to Contribute

1. **Open an issue first** for anything non-trivial. Describe the problem or proposal before writing code. This keeps effort aligned and gives the community a chance to weigh in.
2. **Fork the repository** and create a branch with a descriptive name.
3. **Make your change.** Keep pull requests focused — one concern per PR.
4. **Submit the pull request** referencing the issue it addresses.

For small fixes (typos, broken links, formatting), a direct pull request without a prior issue is welcome.

### The Commands, Step by Step

First time only — fork this repository on GitHub (the Fork button, top right), then:

```bash
# Clone YOUR fork (replace <you> with your GitHub username)
git clone https://github.com/<you>/betat-repo.git
cd betat-repo

# Connect the original repository as "upstream" so you can stay current
git remote add upstream https://github.com/Sylva-AF/betat-repo.git
```

For every contribution:

```bash
# Start from the latest main
git checkout main
git pull upstream main

# Create a branch named for what it does
git checkout -b fix-readme-typo

# ...make your changes, then:
git add .
git commit -m "Fix typo in README problem statement"
git push origin fix-readme-typo
```

Then open the pull request: GitHub will show a "Compare & pull request" button on your fork, or visit your fork's page and start one from your branch into this repository's `main`. Reference the related issue in the description (e.g., "Closes #12").

If the maintainer requests changes, commit and push to the same branch — the pull request updates automatically:

```bash
git add .
git commit -m "Address review comments"
git push origin fix-readme-typo
```

If your fork falls behind while you work:

```bash
git checkout main
git pull upstream main
git push origin main
```

---

## Ground Rules for All Contributions

These follow directly from the project's foundation documents and are not negotiable:

- **The guiding principle is the test.** Every feature must serve provenance, community verification, the HI tag, or barrier-free access. If it serves none of these, it does not belong in Betat (see ARCHITECTURE.md, Guiding Principle).
- **Reading is always public.** No contribution may introduce registration, payment, or any barrier to browsing, searching, or reading.
- **The store is append-only.** No contribution may add delete or update operations on accepted provenance records.
- **Terminology is exact.** Use *Provenancier* and *Contributor* precisely as defined. The `provenancier` field name and the `hi_tag` field are permanent (see PROVENANCE_SPEC.md, Versioning).
- **Security over elegance.** Where a design choice trades security or record integrity for convenience or aesthetics, security wins.
- **The Betat Baseline is a floor.** Communities and code may strengthen it; no contribution may weaken, waive, or bypass it (see COMMUNITY_FRAMEWORK.md, The Betat Baseline).
- **Definition of done includes docs.** A pull request that adds or changes a public capability — a CLI command, an API endpoint, a framework function — must update its runnable snippet on the [Framework Reference](framework-reference.html) pages (or add one, if none exists yet). A capability without a documented example is not finished (see COMMUNITY_FRAMEWORK.md, Documentation Standard).

---

## Changing the Provenance Specification

[PROVENANCE_SPEC.md](PROVENANCE_SPEC.md) carries stricter rules than ordinary code:

- Fields may be **added** in minor versions (0.2, 0.3, ...)
- Fields may **never be removed** without a major version bump and a migration path
- **Breaking changes require community consensus** through the issue and pull request process
- `hi_tag` may never be removed or made optional
- The `provenancier` field name is permanent

Propose spec changes as issues labeled `spec` before opening a pull request.

---

## Technology Choices

The seed stack (Python/Django; SQLite at install, PostgreSQL in production; plain HTTPS + JSON federation — see ARCHITECTURE.md, Seed Technology Stack) is a recommended starting point, not a constraint. The framework is optional; the protocols are mandatory: reference implementations in any language or framework are welcome, provided they conform to the protocols. The protocols are what must remain consistent; the technology beneath them is always open to change by community consensus.

---

## Code of Conduct

All participation in this repository is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

---

*Betat. The human record, for the other person.*
