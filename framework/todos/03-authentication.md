# TODO 03 — Authentication Plugins & Floor

> Status: done — all acceptance criteria pass (37/37 tests, `manage.py check` clean); see "Session handoff" at bottom of this file for design decisions
> Blueprint: [§3](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Authentication (pluggable, floored)"
> Depends on: 01, 02 · Blocks: 04

## Goal
The `communityauth` app: pluggable authentication with a hard floor — at least one method from the protocol list, never zero, never an off-list substitute.

## Tasks
- [x] `AuthMethod` base/protocol: `enroll(applicant)`, `authenticate(credentials)` → identity | rejection
- [x] Seed plugins: `PeerVouchAuth`, `CryptoKeyAuth`, `InstitutionalAuth`
- [x] Floor enforcement at config load: ≥1 configured method, all from the protocol list; else refuse to start
- [x] `/betat/enroll` endpoint (DRF)
- [x] Record the method so `provenancier.authentication_method` can be populated by §04
- [ ] Roadmap stubs (not shipped): `GovernmentIdAuth`, `BehavioralAuth` — intentionally not built (roadmap, out of scope)

## Acceptance criteria
- [x] each seed plugin enrolls + authenticates (`tests/test_communityauth.py`, 15 tests, passing)
- [x] zero-method config rejected at startup (`checks.py` system check; `validate_floor` unit-tested; `manage.py check` runs clean)
- [x] off-list method rejected (tested)
- [ ] method name propagates into a built record (verified in §04 tests — pending §04, out of scope here)

## Security notes
- Peer-vouch is the weakest floor method — its strength is visible in the record, by design; do not hide it
- Token issuance on successful auth follows DRF token patterns; no custom crypto

## Out of scope
- Verification of the *content's* human origin (§04) — that is distinct from authenticating the person
- Government-ID / behavioral methods (roadmap)

## Session handoff (code complete — developer action needed to finish)

Two BLUEPRINT.md Decision Log entries (§03, dated 2026-08) already resolved the two biggest spec gaps:
- Peer-vouch threshold N = **2**, default, community-configurable, never lower.
- The identity object `enroll()`/`authenticate()` return must carry **exactly** the PROVENANCE_SPEC `provenancier` fields (`identity`, `identity_type`, `authentication_method`, `display_name`) — no extras.

### Design decisions made across this section's sessions (not yet in BLUEPRINT Decision Log — consider adding)
- **Floor enforcement mechanism:** Django's System Check Framework (`communityauth/checks.py`, `@register`, wired via `communityauth/apps.py`'s `ready()`), not `AppConfig.ready()` DB queries — checks run automatically before `runserver`/`migrate`/`manage.py check`. The check function queries `CommunityConfig` defensively, swallowing `OperationalError`/`ProgrammingError` for pre-migration state, and no-ops if no config exists yet.
- **CryptoKeyAuth verification:** real Ed25519 signature verification via the `cryptography` package (PyCA). `enroll()`: applicant signs their own public key as a self-signed proof-of-possession (stateless, no server-side nonce). `authenticate()`: caller supplies `message` + `signature`; **replay protection is NOT implemented** — the caller must include a fresh nonce/timestamp in what they sign. Documented simplification for the seed implementation — flag it in docs when §11 happens.
- **InstitutionalAuth verification:** same Ed25519 scheme, keyed by a per-institution public key from `CommunityConfig.trusted_institutions` (JSONField: `{institution_id: public_key_hex}`). `authenticate()` re-verifies against the *current* trusted_institutions entry, not just the value at enroll time — an institution that's removed or rekeyed stops authenticating its previously-enrolled members.
- **Provenancier model:** 1:1 with a Django `User` purely to hang a `rest_framework.authtoken.models.Token` off it. Each plugin's `enroll()` handles the *full* enrollment — validate + persist (User + Provenancier + Token, via `enrollment.persist_provenancier()`) + return identity.
- **Cross-app dependency:** `core/models.py`'s `validate_auth_methods` now imports `communityauth.floor.validate_floor` (lazy import, inside the function, to avoid app-load-order issues) to enforce protocol-list membership at the model level too — closing the gap TODO 02 deliberately left open. This makes `core` depend on `communityauth` at validation time — acceptable since both ship in the same package (BLUEPRINT §0 Decision Log "API structure").
- **`/betat/enroll` API:** `EnrollRequestSerializer` only validates the envelope (`method` + `applicant` dict) — `applicant`'s shape is plugin-specific and validated by the plugin itself. `common/errors.py` now exists (`error_response()`), implementing the standard error shape for the first time — later apps (§04/§06) should reuse it rather than re-inventing.
- **Fixed a pre-existing bug:** `plugins/peer_vouch.py`'s `enroll()` was returning a tuple `(ProvenancierIdentity, token)`, violating the `AuthMethod` contract — now returns just `ProvenancierIdentity`; the `/betat/enroll` view looks the token up itself via `Token.objects.get(user=...)`.

### Files written this section (final state)
- `pyproject.toml` — `cryptography>=42` dependency
- `betat_community/settings.py` — `rest_framework.authtoken` in `INSTALLED_APPS`; `REST_FRAMEWORK` setting (`TokenAuthentication`, `AllowAny` default)
- `betat_community/urls.py` — mounts `POST /betat/enroll`
- `betat_community/common/errors.py` — `error_response()`, the standard `{"error": {...}}` shape
- `communityauth/identity.py`, `base.py`, `crypto.py`, `models.py` (`Provenancier`), `enrollment.py`, `floor.py`, `checks.py`, `apps.py` (wires `checks` via `ready()`)
- `communityauth/plugins/peer_vouch.py`, `crypto_key.py`, `institutional.py`
- `communityauth/api/serializers.py`, `communityauth/api/views.py` (`EnrollView`)
- `core/models.py` — added `CommunityConfig.peer_vouch_threshold` (default 2, `MinValueValidator(2)`) and `trusted_institutions` (JSONField, default dict); wired `validate_auth_methods` to `communityauth.floor.validate_floor`
- `framework/tests/test_communityauth.py` — new, covers everything in "Still to do" item 10 below
- `framework/tests/test_core.py` — fixed: its `_init()` fixture used a placeholder `"peer_vouch"` auth-method string that predates the protocol list; now uses the real `"community_peer_vouching"` method name, since `validate_auth_methods` now actually enforces list membership and would otherwise reject it

### Closed out
Developer ran `pip install -e "./framework[dev]"` (picked up the `cryptography` dependency added mid-section), then `makemigrations core communityauth` + `migrate`, then the full suite: **37/37 passed**, `manage.py check`: **clean**. Section done — next up is §04 (workflow), which depends on this section's `AuthMethod`/`ProvenancierIdentity` contract and `/betat/enroll`.

### Addendum (§10 session, 2026-08) — bug fixed post-close
`EnrollView` (`communityauth/api/views.py`) never checked the requested `method` against `CommunityConfig.auth_methods`, only against the global `PROTOCOL_LIST` — so a community that enabled only one method would still silently accept enrollments via any other protocol-list method. Fixed with a `method_not_enabled` rejection + regression test in `test_communityauth.py`, found while building `tests/test_acceptance.py` (§10). Full rationale: BLUEPRINT §10 Decision Log. Doesn't change this section's status — noted here so a future reader of this file knows the code moved after "done" was declared.
