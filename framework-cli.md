---
title: Framework CLI
parent: For Builders
nav_order: 6
---

# CLI Commands

The `betat` CLI is a thin dispatcher over Django management commands — every command below also runs as `python manage.py <command>` from `framework/`.

## `betat init`

Declares this install's community identity and writes its `CommunityConfig` — the one thing every other endpoint below depends on existing. Also runs an environment preflight (Python 3.11+, SQLite available), checks the declared community id resolves in DNS, and collects an operator good-faith declaration + contact email (written to `.env` as an accountability record — never used operationally). The declaration and email prompts are **not skippable**, even when the identity fields below are supplied as flags — this is deliberate: a script can't fabricate a resolving domain or a human's acceptance of the declaration.

```
$ betat init --id marinebiology-lagos.org --name "Marine Biology Lagos" \
    --domain "marine biology" --content-type scientific_observation \
    --store-uri https://marinebiology-lagos.org/betat/records \
    --auth-method community_peer_vouching
...
Do you accept this declaration? [yes/no]: yes
Contact email: operator@marinebiology-lagos.org
...
CommunityConfig written for 'marinebiology-lagos.org'.

Readiness:
  [x] identity declared — id=marinebiology-lagos.org
  [x] HI standard — human-originated, community-verified
  [x] auth method(s) — community_peer_vouching
```

Every flag can be omitted for a fully interactive run instead. `--auth-method` is repeatable to enable more than one authentication method — at least one from the protocol list is required (`community_peer_vouching`, `cryptographic_signature`, `institutional_endorsement`).

### Database configuration

`betat init` declares community identity — the database engine is separate, set via the `BETAT_DB` environment variable and read directly by `settings.py`. No `BETAT_DB` set at all means SQLite (`betat.sqlite3` in the project directory) — zero configuration, fine for evaluation. Point `BETAT_DB` at a PostgreSQL connection before a real deployment; PostgreSQL is the only engine where append-only is enforced at the database-permission level rather than by guard triggers (a full production setup guide is upcoming).

## `betat runserver` / `betat check`

Plain aliases for `manage.py runserver` / `manage.py check` — nothing framework-specific to document beyond standard Django behavior.

## `betat announce`

Pings the registry: "new records available — crawl me now" (see [API Endpoints](framework-api.html) for what communities publish; the registry itself is betat main's job, not this package's). Requires `BETAT_REGISTRY_URL` to be set — there is no default, since the registry's own announce contract isn't published yet.

```
$ export BETAT_REGISTRY_URL=https://registry.example.org/announce
$ betat announce
Announced 'marinebiology-lagos.org' to the registry.
Payload: {'community_id': 'marinebiology-lagos.org', 'store_uri': 'https://marinebiology-lagos.org/betat/records', 'announced_at': '2026-09-01T12:00:00Z'}
```

Can also fire automatically after every accepted submission — set `BETAT_AUTO_ANNOUNCE=true` (off by default; a slow or unreachable registry will never block or fail an accept, it just logs a warning).

## `betat export`

Produces an integrity-verifiable dump of every provenance record this community has issued — every record's `record_id` recomputes, and the whole bundle carries a `export_hash` so a reader can tell if the file itself was altered in transit (see [core/export.py](https://github.com/Sylva-AF/betat-repo) for exactly what "signed" means here — a recomputable hash, not a private-key signature; there is no community signing key in the seed implementation).

```
$ betat export --output betat-export.json
Exported 42 record(s) to betat-export.json
```

Omit `--output` to print the JSON to stdout instead — useful for piping straight into another tool.

```json
{
  "betat_export_version": "0.1",
  "community": {"id": "marinebiology-lagos.org", "name": "Marine Biology Lagos", "...": "..."},
  "exported_at": "2026-09-01T12:00:00Z",
  "record_count": 42,
  "records": [ /* every record, exactly as PROVENANCE_SPEC.md defines it */ ],
  "export_hash": "sha256:9f4a2b..."
}
```
