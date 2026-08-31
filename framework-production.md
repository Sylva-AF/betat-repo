---
title: Production Guide
parent: For Builders
nav_order: 9
---

# Production Guide

The default install (`pip install betat-community`, no environment configured) runs entirely on SQLite — zero configuration, fine for evaluation, and the SQLite guard triggers ([Store Functions](framework-store.html)) enforce append-only for that engine. This page is for the one thing that changes when a community goes live: **PostgreSQL**, where append-only becomes a database-permission guarantee instead of a trigger.

**The only production step is setting `BETAT_DB` to a PostgreSQL connection URL and deploying — no code changes, no editing the installed package.** `settings.py` reads `BETAT_DB` directly; everything below is what that means concretely.

## 1. Create the database and two roles

PostgreSQL table **owners** always retain UPDATE/DELETE regardless of GRANT/REVOKE — ownership privileges can't be revoked, only reassigned. So genuine append-only enforcement needs **two roles**, not one:

- a **migrator** role that owns the schema and runs `migrate` (used only at deploy time)
- a restricted **app** role that the running server actually connects as — granted INSERT/SELECT only, never UPDATE/DELETE

```sql
-- as a PostgreSQL superuser
CREATE DATABASE betatdb;

CREATE ROLE betat_migrator LOGIN PASSWORD '<migrator-password>';
GRANT ALL PRIVILEGES ON DATABASE betatdb TO betat_migrator;

CREATE ROLE betat_app LOGIN PASSWORD '<app-password>';
GRANT CONNECT ON DATABASE betatdb TO betat_app;
```

## 2. Run migrations as the migrator role

`betat init` (run once, during evaluation) writes a standard `manage.py` to your working directory — from that point forward it's plain Django, no wrapper needed:

```
$ BETAT_DB=postgres://betat_migrator:<migrator-password>@localhost:5432/betatdb \
  python manage.py migrate
```

This creates every table, owned by `betat_migrator`.

## 3. Lock the app role down to INSERT/SELECT

Run this once, after migrating, as a role with privilege to grant on the schema (the migrator role, or a superuser):

```sql
GRANT USAGE ON SCHEMA public TO betat_app;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO betat_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO betat_app;
REVOKE UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM betat_app;

-- so future migrations' new tables inherit the same restriction automatically
ALTER DEFAULT PRIVILEGES FOR ROLE betat_migrator IN SCHEMA public
  GRANT SELECT, INSERT ON TABLES TO betat_app;
```

`betat_app` can now never UPDATE or DELETE `store_provenancerecord` (or anything else) at the database-permission level — the real append-only boundary, stronger than the SQLite guard triggers.

## 4. Run the server as the app role

```
$ BETAT_DB=postgres://betat_app:<app-password>@localhost:5432/betatdb \
  betat runserver
```

Re-run migrations (step 2, as `betat_migrator`) whenever a framework upgrade ships new migrations; the running server process always uses the restricted `betat_app` credentials.

## Moving existing data from a SQLite evaluation install

```
$ python manage.py dumpdata store --output=records.json    # against the old SQLite install (BETAT_DB unset)

$ BETAT_DB=postgres://betat_migrator:<migrator-password>@localhost:5432/betatdb \
  python manage.py loaddata records.json                   # as the migrator role, before step 3 locks it down
```

Load the data before running step 3 — `loaddata` performs inserts, so it works under either role, but doing it before the app role is locked down keeps the sequence simple and avoids needing migrator credentials again later.

## Python version

Tested on the 3.11 floor through 3.12+. No production-specific version constraint beyond what `pyproject.toml` already declares.

---

See also: [Framework Reference](framework-reference.html) · [Store Functions](framework-store.html) (the SQLite append-only mechanism this page's PostgreSQL role setup replaces).
