# TODO 02 — Config & Community Identity

> Status: not started
> Blueprint: [§2](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Community Identity", "CommunityConfig"
> Depends on: 01 · Blocks: 03, 04, 06, 08

## Goal
The `core` app: a community declares who it is (FQDN id), what standard it holds (≥ baseline), and how it authenticates — via `betat init`. This config is the identity every record inherits.

## Tasks
- [ ] `core/models.py`: `CommunityConfig` (id, name, domain, content_type, hi_standard, auth_methods, store_uri)
- [ ] FQDN id validator: lowercase, valid domain syntax, non-empty labels; reject otherwise
- [ ] Baseline renderer: default `hi_standard = "human-originated, community-verified"`; additions are strengthen-only (never replace/weaken)
- [ ] `init` management command (guided): collects fields, declares (not verifies) domain control, writes config
- [ ] Print readiness checklist + "verification happens at the registry (TXT challenge, roadmap)" note
- [ ] Single-config-per-install for seed (documented assumption)

## Acceptance criteria
- [ ] `betat init` writes a valid `CommunityConfig`
- [ ] malformed FQDN id rejected with the standard error shape
- [ ] baseline always present; config can extend but not remove/weaken it
- [ ] chosen auth method(s) must be from the protocol list (enforced with §03)

## Security notes
- `init` never claims to prove domain ownership — it declares; the registry verifies. Wording must not overstate.
- No secret material printed to stdout

## Out of scope
- Serving `/betat/info` (§06) — that reads this config but belongs to federation
- The auth plugins themselves (§03)
