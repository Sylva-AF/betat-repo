---
title: Framework Reference
parent: For Builders
nav_order: 5
---

# Framework Reference

Runnable documentation for the `betat-community` package (`framework/` in this repo) — every CLI command, every `/betat/` API endpoint, and the Python `store` functions, each with the actual call and real output. This is the "Documentation Standard" from [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md): a capability without a runnable snippet isn't considered finished.

- **[CLI Commands](framework-cli.html)** — `betat init`, `runserver`, `check`, `announce`, `export`
- **[API Endpoints](framework-api.html)** — the full `/betat/` surface: enroll, submit, queue, review, info, records, changes
- **[Store Functions](framework-store.html)** — the Python `store.py` module, for anyone extending the framework in-process

Install first: `pip install -e "./framework[dev]"` from the repo root (see [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md) → What an Operator Gets).
