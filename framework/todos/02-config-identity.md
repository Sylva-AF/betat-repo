# TODO 02 — Config & Community Identity

> Status: done (auth_methods protocol-list membership intentionally deferred to §03 — see note below)
> Blueprint: [§2](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Community Identity", "CommunityConfig"
> Depends on: 01 · Blocks: 03, 04, 06, 08

## Goal
The `core` app: a community declares who it is (FQDN id), what standard it holds (≥ baseline), and how it authenticates — via `betat init`. This config is the identity every record inherits.

## Tasks
- [x] `core/models.py`: `CommunityConfig` (id, name, domain, content_type, hi_standard, auth_methods, store_uri)
- [x] FQDN id validator: lowercase, valid domain syntax, non-empty labels; reject otherwise
- [x] Baseline renderer: default `hi_standard = "human-originated, community-verified"`; additions are strengthen-only (never replace/weaken)
- [x] `init` management command (guided): collects fields, declares (not verifies) domain control, writes config
- [x] Print readiness checklist + "verification happens at the registry (TXT challenge, roadmap)" note
- [x] Single-config-per-install for seed (enforced in `CommunityConfig.clean()`, not just documented)
- [x] Migration — `core/migrations/0001_initial.py` generated and applied by developer

## Acceptance criteria
- [x] `betat init` writes a valid `CommunityConfig`
- [x] malformed FQDN id rejected with the standard error shape (`ValidationError(message, code=...)`, surfaced as `CommandError` in the CLI)
- [x] baseline always present; config can extend but not remove/weaken it
- [ ] chosen auth method(s) must be from the protocol list (enforced with §03) — **partial**: `auth_methods` is validated as a non-empty list of strings now; membership against the actual protocol list is the "floor rule enforced in config load" that BLUEPRINT §3 assigns to `communityauth`, so it's deliberately not implemented here to avoid inventing method identifiers ahead of §03

## Tests
- `framework/tests/test_core.py`: valid init, malformed FQDN, second-init rejection, hi_standard strengthen-only (CLI + model level), empty auth_methods rejection. 6/6 passing (developer-verified).

## Security notes
- `init` never claims to prove domain ownership — it declares; the registry verifies. Wording must not overstate.
- No secret material printed to stdout

## Out of scope
- Serving `/betat/info` (§06) — that reads this config but belongs to federation
- The auth plugins themselves (§03)
