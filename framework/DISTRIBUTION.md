# DISTRIBUTION.md — Betat Community Framework

How the framework is packaged, built, and distributed.
Read this before starting TODO 12 (packaging).

---

## Who this is for

Anyone who wants to distribute a new release of the framework,
or understand why distribution works the way it does.

---

## The core principle

A community organizer who reads about Betat on LinkedIn, visits betat.org,
and decides to install the framework should be able to do so without a
GitHub account, without registering anywhere, and without any step beyond
having Python 3.11 installed. The distribution design is built around that
person.

---

## What ships

**The package ships SQLite only.**

SQLite is built into Python's standard library. An operator installs the
framework and gets a working provenance registry immediately — no database
server to provision, no connection URL to configure, no infrastructure
decisions before they can evaluate whether Betat fits their community.

PostgreSQL is the recommended production database, but the framework never
installs or manages a PostgreSQL server. When an operator is ready for
production, they provision their own database (on their host, in their
cloud, or via a managed service), set the `BETAT_DB` environment variable
to their connection URL, and the framework connects. That is the entire
production step — no code changes, no framework updates needed.

**What this means for settings.py:**

> **Correction (§12, 2026-08):** this section originally said the `BETAT_DB`
> env var check and `dj_database_url` call must be stripped from `settings.py`
> before packaging, leaving a hardcoded-SQLite version in the wheel. That
> doesn't actually work: once `betat-community` is `pip install`ed (not an
> editable checkout), `settings.py` lives inside `site-packages/` — there is
> no supported place for an operator to "add it themselves" without hand-
> patching a library file, which breaks on every upgrade. Corrected below.
> Full rationale: `framework/BLUEPRINT.md` §12 Decision Log.

`settings.py` **ships with `BETAT_DB`/`dj_database_url` support built in,
permanently** — it is not stripped before building. No `BETAT_DB` set means
SQLite, zero configuration (`betat.sqlite3` next to the installed package,
or wherever `BETAT_DB` points). Set `BETAT_DB` to a full PostgreSQL
connection URL (`postgres://user:pass@host:5432/db`) and the same installed
package connects to PostgreSQL — no code changes, no editing installed
files. This is what makes "What the operator experiences" step 9 below
actually true for a `pip install`ed package.

`psycopg[binary]` and `dj-database-url` are therefore plain `dependencies`
in `pyproject.toml`, not an optional extra — `settings.py` imports
`dj_database_url` unconditionally, so it must always be present, even for
operators who never leave SQLite.

---

## Distribution channels

### Primary — PyPI

The package is published to the Python Package Index (pypi.org). Operators
install with:

```bash
pip install betat-community
```

No GitHub account needed. No registration. No extra pip configuration.
PyPI is the default index pip checks, so this single command is the
complete install step for any operator with Python 3.11+.

The betat.org For Builders documentation shows this command as the install
step. A visitor from any context — LinkedIn, a conference, a colleague's
recommendation — follows the link to betat.org, reads one command, and
has the framework.

**Before the first publish:** register the `betat-community` name on
pypi.org. Create a PyPI account (one-time, as the publisher) and verify
the name is available. If another package claims the name first, changing
it after operators have installed it is painful. The name is declared in
`pyproject.toml` — claim it on PyPI before the v0.1 release.

### Secondary — GitHub Release assets

Each release also publishes the built `.whl` and `.tar.gz` files as
GitHub Release assets on `Sylva-AF/betat-repo`. These are publicly
downloadable without a GitHub account — a direct link from betat.org
points here as a fallback for:

- Operators in environments where pip access to PyPI is restricted
  (corporate firewalls, air-gapped systems)
- Operators who prefer downloading a file manually over running a
  pip install command

The release asset URL format is:
`https://github.com/Sylva-AF/betat-repo/releases/download/v{version}/betat_community-{version}-py3-none-any.whl`

Link to this from the betat.org download section once the first release
is published.

---

## How to build and publish (manual process)

The build and upload process is manual — the developer runs it
deliberately for each release. This keeps the release process fully
under human control, consistent with the working model that consequential
actions are the developer's responsibility.

**Prerequisites (one-time setup):**

```bash
pip install build twine
```

Create a PyPI account at pypi.org and generate an API token
(Account Settings → API tokens → Add API token, scope to the
`betat-community` project). Store the token securely — you will
need it for the upload step.

**Pre-release checklist (do these before building):**

- [ ] Run the dual-DB ship gate: store and acceptance suites pass on
      both SQLite and PostgreSQL (BLUEPRINT §0 dual-database ship promise) —
      point `BETAT_DB` at a real PostgreSQL instance and re-run `pytest
      tests/`; the two SQLite-guard-trigger tests are a permanent, by-design
      skip on PostgreSQL (role revocation is documented `psql`, not shipped
      migration code — see framework-production.md), everything else must pass
- [ ] Update `version` in `pyproject.toml` to the release version
- [ ] Confirm `.gitignore` excludes `dist/`, `*.egg-info/`, `__pycache__/`
- [ ] Confirm `framework/README.md` exists and describes the package
      accurately (PyPI uses this as the package description page)
- [ ] Run `python manage.py check` — no errors

**Build the package:**

```bash
# from the repo root, with the venv active
python -m build ./framework
```

This produces two files in `framework/dist/`:
- `betat_community-{version}-py3-none-any.whl` — the wheel (preferred)
- `betat_community-{version}.tar.gz` — the source distribution

**Verify before uploading:**

```bash
twine check framework/dist/*
```

This checks the package metadata is valid and the description renders
correctly on PyPI. Fix any warnings before uploading — they are harder
to fix after the package is live.

**Upload to PyPI:**

```bash
twine upload framework/dist/*
```

When prompted, use `__token__` as the username and paste your API token
as the password. Or configure `~/.pypirc` to store these so you are not
prompted each time.

**Attach to GitHub Release:**

1. Go to `github.com/Sylva-AF/betat-repo/releases/new`
2. Tag the release: `v{version}` (e.g. `v0.1.0`)
3. Title: `Betat Community Framework v{version}`
4. Attach `framework/dist/*.whl` and `framework/dist/*.tar.gz` as
   release assets
5. Write release notes summarising what changed
6. Publish the release

**After publishing:**

- Verify the PyPI page: `https://pypi.org/project/betat-community/`
- Test a clean install in a fresh virtual environment:
  ```bash
  python3.11 -m venv /tmp/betat-test
  source /tmp/betat-test/bin/activate
  pip install betat-community
  betat --help
  betat init
  ```
- Update betat.org install documentation if the install command or
  steps changed
- Link the GitHub Release asset from betat.org's download section

---

## Package metadata (pyproject.toml)

Before the first PyPI publish, these fields should be complete in
`[project]` in `pyproject.toml`:

```toml
[project]
name = "betat-community"
version = "0.1.0"
description = "Reference community framework for Betat — provenance of human-originated content."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Ateafac Forsong" }]
keywords = ["provenance", "human-intelligence", "betat", "HI", "content-verification"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Django",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Topic :: Internet :: WWW/HTTP",
]

[project.urls]
Homepage = "https://betat.org"
Documentation = "https://betat.org/for-builders.html"
Repository = "https://github.com/Sylva-AF/betat-repo"
"Bug Tracker" = "https://github.com/Sylva-AF/betat-repo/issues"
```

The `classifiers` and `[project.urls]` sections make the PyPI page
informative and help operators find the project. PyPI renders them
as structured metadata on the package page.

---

## What the operator experiences

To make sure the distribution design serves its intended audience,
here is the complete path from discovery to running framework:

1. Operator reads about Betat (LinkedIn, betat.org, word of mouth)
2. Visits betat.org → For Builders → Getting Started
3. Sees: `pip install betat-community`
4. Runs it — Django, DRF, and the framework install in one command
5. Runs `betat init` — guided setup, DNS check on domain, declaration,
   email, CommunityConfig written, .env accountability record written
6. Runs `python manage.py migrate` — database tables created
7. Runs `python manage.py createsuperuser` — first verifier account
8. Runs `python manage.py runserver` — framework is live
9. When ready for production: provisions PostgreSQL, sets `BETAT_DB`,
   follows the production guide on betat.org

No GitHub account required at any step. No decisions forced before the
framework is running. The SQLite default means step 6 just works.

---

## Future work (not in scope for v0.1)

- Automated GitHub Actions publish pipeline (triggers on version tag,
  runs tests, builds and uploads to PyPI automatically)
- Docker image (`docker run betat/community`) for operators who want
  a fully self-contained environment
- Homebrew formula or apt package for non-Python operators
- Versioned documentation on betat.org (v0.1 docs, v0.2 docs)

These are deliberately out of scope for the initial release. The manual
process and PyPI distribution are sufficient to get the framework into
operators' hands. Automation comes when the release cadence justifies it.

---

*Betat. The human record, for the other person.*
