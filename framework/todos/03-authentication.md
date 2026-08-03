# TODO 03 — Authentication Plugins & Floor

> Status: not started
> Blueprint: [§3](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Authentication (pluggable, floored)"
> Depends on: 01, 02 · Blocks: 04

## Goal
The `communityauth` app: pluggable authentication with a hard floor — at least one method from the protocol list, never zero, never an off-list substitute.

## Tasks
- [ ] `AuthMethod` base/protocol: `enroll(applicant)`, `authenticate(credentials)` → identity | rejection
- [ ] Seed plugins: `PeerVouchAuth`, `CryptoKeyAuth`, `InstitutionalAuth`
- [ ] Floor enforcement at config load: ≥1 configured method, all from the protocol list; else refuse to start
- [ ] `/betat/enroll` endpoint (DRF)
- [ ] Record the method so `provenancier.authentication_method` can be populated by §04
- [ ] Roadmap stubs (not shipped): `GovernmentIdAuth`, `BehavioralAuth`

## Acceptance criteria
- [ ] each seed plugin enrolls + authenticates (tests)
- [ ] zero-method config rejected at startup
- [ ] off-list method rejected
- [ ] method name propagates into a built record (verified in §04 tests)

## Security notes
- Peer-vouch is the weakest floor method — its strength is visible in the record, by design; do not hide it
- Token issuance on successful auth follows DRF token patterns; no custom crypto

## Out of scope
- Verification of the *content's* human origin (§04) — that is distinct from authenticating the person
- Government-ID / behavioral methods (roadmap)
