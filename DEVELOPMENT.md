# DEVELOPMENT.md — Betat Community Framework

Local development setup guide for contributors and operators testing
before deployment. This is distinct from `DISTRIBUTION.md` (which covers
shipping) and `start-a-community.md` (which covers operator installation).

Read `framework/CLAUDE.md` and `framework/BLUEPRINT.md §0` before
starting a build session. This file covers environment setup only.

---

## Prerequisites

- Python 3.11 installed via your OS package manager (not compiled from source)
- Git configured for the Sylva-AF account (SSH key `id_ed25519_sylva`)
- The `betat-sandbox` Docker container built (`docker build -t betat-sandbox .`)
- A terminal inside the container with `--network host` for PostgreSQL access

Verify Python 3.11 is the right build before creating a virtualenv:

```bash
python3.11 --version
# Must show Python 3.11.x

python3.11 -c "import sqlite3; print('sqlite ok')"
# Must print: sqlite ok
# If this fails, your Python was compiled from source without SQLite.
# Install via package manager: dnf install python3.11  (Rocky/RHEL)
#                              apt install python3.11  (Ubuntu/Debian)
#                              brew install python@3.11 (macOS)
```

---

## Step 1 — Start the sandbox container

```bash
# From the host machine:
docker run -it --rm \
    --name betat-build \
    -v ~/betat-repo:/workspace \
    -w /workspace/framework \
    --network host \
    --cap-drop ALL --cap-add SETUID --cap-add SETGID --cap-add DAC_OVERRIDE \
    betat-sandbox \
    bash
```

`--network host` is required for PostgreSQL access during dual-DB testing.
`--cap-add DAC_OVERRIDE` is required too: the bind-mounted repo is owned by
your host user (not root), and without this capability root inside the
container cannot write to it at all — every `pip install`, `.env` write,
`betat init`, even `touch`, fails with `Permission denied` despite the
container prompt showing `[root@...]`. This is not optional.

All following commands run inside the container unless noted otherwise.

---

## Step 2 — Fresh virtualenv

If a `.venv` already exists from a previous session, remove it first.
A venv is tied to the Python that built it — never reuse one across
Python versions or across host/container boundaries. **This step must run
after Step 1, inside the container.** Building the venv on the host and
then entering the container (or vice versa) leaves `.venv/bin/python`
symlinked to a binary path that doesn't exist on the other side, and every
command reports `python: command not found` even though the venv appears
active.

```bash
# Inside the container, at /workspace:
cd /workspace

# Remove old venv if present
deactivate 2>/dev/null; rm -rf .venv

# Create fresh venv with Python 3.11
python3.11 -m venv .venv

# Activate it — do this every time you open a new shell
source .venv/bin/activate
# Prompt shows (.venv) — confirms activation

# Verify
python --version              # must show Python 3.11.x
python -c "import sqlite3; print('sqlite ok')"   # must print sqlite ok
pip install --upgrade pip
```

**Every new shell into the container needs re-activation:**
```bash
source /workspace/.venv/bin/activate
```

**Which side am I on?** When unsure whether you are inside the container
or on the host:
```bash
ls /.dockerenv && echo "INSIDE container" || echo "ON host"
```

Container prompt looks like: `[root@5a01f44af990 framework]`
Host prompt looks like: `[sylva@www betat-repo]`

---

## Step 3 — Install the framework

Run this from **`/workspace`** (the repo root), not `/workspace/framework`
— even though Step 1's container starts you in `framework/`. The install
path `./framework[dev]` is relative to the repo root; running it from
inside `framework/` points at a nonexistent nested `framework/framework`
and fails.

```bash
cd /workspace
pip install -e "./framework[dev]"
# Installs Django, DRF, pytest, pytest-django, and all dependencies.
# The -e flag installs in editable mode — code changes take effect
# immediately without reinstalling.
# Django equivalent: pip install django djangorestframework pytest
```

Confirm the install:
```bash
python -c "import django; print('django', django.get_version())"
betat --help
# Should list: init, runserver, check, announce, export, start, backup
```

---

## Step 4 — DNS override for development

The community id DNS check (`socket.getaddrinfo`) requires a real
resolving domain when run interactively. Two approaches for development:

### Approach A — /etc/hosts override (for the interactive prompts or the browser wizard)

Run this on the **host machine** (not inside the container).
The container uses `--network host` so host DNS is visible inside:

```bash
# On the HOST, in a separate terminal:
sudo sh -c 'echo "127.0.0.1 betat-dev.local" >> /etc/hosts'
sudo sh -c 'echo "127.0.0.1 science.betat-dev.local" >> /etc/hosts'
sudo sh -c 'echo "127.0.0.1 archive.betat-dev.local" >> /etc/hosts'

# Verify from inside the container:
python3 -c "import socket; socket.getaddrinfo('betat-dev.local', None); print('resolves ok')"
```

Use `betat-dev.local` as your community id during `betat init` and
the setup wizard. The subdomains let you test multiple community ids
in the same dev session.

### Approach B — non-interactive flags (fastest path, no /etc/hosts needed)

There is no `BETAT_SKIP_DNS_CHECK` env var — `init.py` doesn't implement
one. Instead, pass `--id` (and the other required fields) directly to
`betat init` rather than answering the interactive prompts: the
non-interactive path only **warns** on a non-resolving domain, it doesn't
block. See Step 7 for the full command. Any string works as `--id`,
resolving or not.

**Use Approach A when you want to walk through the interactive prompts or
the browser setup wizard as an operator would. Use Approach B to get to a
running server fastest.**

---

## Step 5 — Create the .env file

`betat init` writes `.env` during setup (`BETAT_SECRET_KEY`,
`BETAT_OPERATOR_EMAIL`, etc. — see `framework/.env.example` for the full
reference), but for development create it first with the dev-relevant
values. All variables `settings.py` reads are `BETAT_`-prefixed —
`SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` (no prefix) are **not** read by
anything and silently do nothing.

Use `printf`, not a heredoc — pasting a multi-line `cat > .env << 'EOF'`
block into some terminals auto-indents the pasted lines, which shifts the
closing `EOF` off column 0 and leaves the shell hung at a `>` prompt
waiting for a delimiter that will never match. `Ctrl-C` breaks out of that
if it happens.

```bash
# From /workspace/framework:
printf '%s\n' \
  'BETAT_DEBUG=true' \
  'BETAT_ALLOWED_HOSTS=localhost,127.0.0.1,betat-dev.local' > .env
```

`betat init` fills in `BETAT_SECRET_KEY` and the accountability fields on
top of this — it never overwrites a key that's already present.

---

## Step 6 — Migrate and create a superuser

**This must run before Step 7 (`betat init`).** `init` checks
`CommunityConfig.objects.exists()` as its first step, which queries a
table that doesn't exist until migrations have run — running `init` first
fails with `no such table: core_communityconfig`.

```bash
python manage.py migrate
# Creates all database tables.
# Run this after every pull that includes new migrations.
# Django equivalent: python manage.py migrate

python manage.py createsuperuser
# Creates the first verifier account.
# Username and password are yours to choose for dev.
# Django equivalent: python manage.py createsuperuser
```

---

## Step 7 — Run betat init

Guided prompts (pairs with Step 4's Approach A):
```bash
cd /workspace/framework
betat init
# Complete the operator declaration and email steps — these are real,
# the same accountability record ships in production.
```

Or non-interactive flags (Step 4's Approach B — faster, no /etc/hosts
needed; still prompts for the operator declaration and email, those
aren't skippable by design):
```bash
betat init --id test.betat-dev.local --name "Test Community" \
  --domain "general testing" --content-type text \
  --store-uri "http://localhost:8000/betat" \
  --auth-method community_peer_vouching
# --content-type must be one of CONTENT_TYPE_CHOICES (core/models.py).
# --auth-method must be one of PROTOCOL_LIST (communityauth/floor.py) —
# community_peer_vouching, cryptographic_signature, institutional_endorsement.
```

Alternatively, run `betat start` first and use the browser wizard at
`http://localhost:8000/community/install/`.

---

## Step 8 — Verify and start

```bash
python manage.py check
# Checks Django configuration for errors.
# In dev (BETAT_DEBUG=true), production warnings are expected and acceptable.
# Django equivalent: python manage.py check
# Production check: python manage.py check --deploy

betat start
# Starts the development server at http://localhost:8000
# Django equivalent: python manage.py runserver 0.0.0.0:8000
# Production server: gunicorn betat_community.wsgi:application
```

Visit `http://localhost:8000/community/` in your browser.

**What you should see:**
- If `CommunityConfig` does not exist yet: the Phase 1 installer screen
  with the eclipse animation
- If `CommunityConfig` exists: the community UI (Records, Enroll, Submit,
  Review queue) with your community name in the nav

---

## Running tests

```bash
# From /workspace/framework, venv active:
pytest tests/ -v
# Runs the full test suite.
# Django equivalent: python manage.py test (pytest-django wraps this)

# Run a specific test file:
pytest tests/test_store.py -v

# Run with PostgreSQL (dual-DB ship gate):
BETAT_DB=postgresql://postgres@localhost:5432/betat pytest tests/ -v
# Requires PostgreSQL running and the betat database created.
# The developer runs this before shipping — not Claude Code.
```

---

## Common development tasks

**Reset the community config and start over:**
```bash
python manage.py shell -c "
from betat_community.core.models import CommunityConfig
CommunityConfig.objects.all().delete()
print('CommunityConfig cleared')
"
# Then run betat init again.
```

**Check what is in the database:**
```bash
python manage.py shell
# Inside the shell:
from betat_community.core.models import CommunityConfig
from betat_community.store.models import ProvenanceRecord
print(CommunityConfig.objects.first())
print(ProvenanceRecord.objects.count())
exit()
# Django equivalent: python manage.py shell (same command)
# DB shell: python manage.py dbshell
```

**Back up the dev database:**
```bash
betat backup
# SQLite: copies betat.sqlite3 to a timestamped backup file.
# Django equivalent: cp betat.sqlite3 betat_backup_$(date +%Y%m%d).sqlite3
```

**Apply new migrations after a pull:**
```bash
git pull                      # developer action
source /workspace/.venv/bin/activate
pip install -e "./framework[dev]"   # in case dependencies changed
python manage.py migrate
```

**Check SSH auth before pushing:**
```bash
ssh-add ~/.ssh/id_ed25519_sylva     # load the Sylva-AF key
ssh -T git@github.com               # confirm: Hi Sylva-AF!
```

---

## Dual-DB testing (before shipping)

Per BLUEPRINT §0 dual-database ship promise, the store and acceptance
test suites must pass on both SQLite and PostgreSQL before v0.1 ships.
The developer runs this — Claude Code does not.

```bash
# 1. Confirm PostgreSQL is accessible (--network host required):
python -c "
import psycopg
psycopg.connect('postgresql://postgres@localhost:5432/postgres',
                connect_timeout=5).close()
print('postgres reachable')
"

# 2. Create the betat database if it does not exist:
# Run on the HOST:
psql -U postgres -c "CREATE DATABASE betat;"

# 3. Run the suite against SQLite (default):
pytest tests/ -v

# 4. Run the suite against PostgreSQL:
BETAT_DB=postgresql://postgres@localhost:5432/betat \
python manage.py migrate && \
BETAT_DB=postgresql://postgres@localhost:5432/betat \
pytest tests/ -v

# Both must pass before shipping.
```

---

## Troubleshooting

**`sqlite3` import fails:**
Your Python 3.11 was compiled from source without SQLite.
Install via OS package manager (see Prerequisites above).

**`pip: command not found` after entering the container:**
The venv is not active. Run `source /workspace/.venv/bin/activate`.

**`python: command not found` even though the venv shows `(.venv)` active:**
The venv was built on the wrong side of the host/container boundary (see
Step 2) — its `bin/python` symlink points at a binary path that doesn't
exist here. Delete it and rebuild inside the container: `rm -rf .venv &&
python3.11 -m venv .venv && source .venv/bin/activate`.

**`Permission denied` writing anywhere under `/workspace`, even as root:**
The container is missing `--cap-add DAC_OVERRIDE` (see Step 1). The
bind-mounted repo is owned by your host user, and without that capability
root inside the container can't bypass ordinary file-permission checks —
it's just another non-owning uid as far as the write check is concerned.

**A pasted `cat > .env << 'EOF' ... EOF` block hangs at a `>` prompt:**
The terminal indented the pasted lines, so the closing `EOF` isn't flush
at column 0 and bash never matches it. `Ctrl-C` to break out, then use the
`printf` form in Step 5 instead of a heredoc.

**`betat-dev.local` does not resolve inside the container:**
The container must be launched with `--network host`.
Check: `ls /.dockerenv` confirms you are inside the container.

**`django.db.utils.OperationalError: no such table: core_communityconfig` from `betat init`:**
`python manage.py migrate` hasn't run yet. Step 6 must come before Step 7
— `init` checks for an existing `CommunityConfig` as its first action.

**`git push` asks for a password:**
The SSH agent does not have the Sylva-AF key loaded.
Run `ssh-add ~/.ssh/id_ed25519_sylva` then retry.

**`CommunityConfig.objects.exists()` returns True but you want a clean start:**
Use the reset command above (manage.py shell -c delete).
The middleware redirects to the installer only when no config exists.

**`manage.py check --deploy` warns about DEBUG=True:**
Expected in development when `BETAT_DEBUG=true` is in `.env`.
Acceptable for dev — resolve before going public.

---

## File reference

| File | Purpose |
|------|---------|
| `framework/BLUEPRINT.md` | Authoritative build decisions — read first |
| `framework/CLAUDE.md` | Session bootstrap for Claude Code |
| `framework/TODO.md` | Build plan and section status |
| `framework/todos/` | Per-section task checklists |
| `framework/DISTRIBUTION.md` | How to ship and publish the package |
| `framework-production.md` | Recommended production stack, PostgreSQL role setup |
| `ROADMAP.md` | Where the project goes after v0.1 |
| `DEVELOPMENT.md` | This file — local dev setup |
| `.env` | Local environment variables (gitignored) |
| `framework/.env.example` | Template for .env (committed, no secrets) |

---

*Betat. The human record, for the other person.*
