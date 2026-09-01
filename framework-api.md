---
title: Framework API
parent: For Builders
nav_order: 7
---

# API Endpoints

Every endpoint speaks plain JSON over HTTPS — no special client needed. Reading is always public and unauthenticated; writing requires the stated token, sent as `Authorization: Token <token>`. Every error uses the same shape: `{"error": {"code": "...", "message": "..."}}`.

**Running locally?** Every example below uses `https://your-community.example` as a stand-in for your actual deployed community. During development, `betat runserver` (or `manage.py runserver`) serves on `http://127.0.0.1:8000` by default — swap the domain for that, and drop `https://` for `http://`. For example, the `/betat/info` call further down becomes:

```bash
curl http://127.0.0.1:8000/betat/info
```

Same substitution applies to every endpoint on this page.

## `POST /betat/enroll` — become a Provenancier

Public. `method` must be on the protocol list *and* enabled by this community (`betat init --auth-method`). Returns a token — save it, it's how you submit.

```bash
curl -X POST https://your-community.example/betat/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "method": "cryptographic_signature",
    "applicant": {
      "identity": "did:key:z6MkfExample",
      "public_key": "3b1c...",
      "signature": "a91f...",
      "display_name": "Ada Lovelace"
    }
  }'
```

```json
{
  "identity": "did:key:z6MkfExample",
  "identity_type": "cryptographic_key",
  "authentication_method": "cryptographic_signature",
  "display_name": "Ada Lovelace",
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

`applicant` fields differ per method: `community_peer_vouching` needs just `identity` (+ optional `display_name`) — see "Two-phase peer-vouch enrollment" below, vouches are no longer supplied by the applicant; `cryptographic_signature` needs `public_key` + a self-signed `signature` (proof of possession — sign your own public key), *or* a `passphrase` instead of both (see below); `institutional_endorsement` needs `institution_id` + the institution's `signature` over your identity.

### Generating a keypair for `cryptographic_signature`

**Option A — passphrase (no technical step, recommended for most applicants).** The bundled UI's enroll form accepts a `passphrase` field instead of a pasted `public_key`/`signature`: the server derives a deterministic Ed25519 keypair from it (scrypt, salted per-community — the same passphrase yields a different key on every community) and self-signs the proof itself. The private key is never persisted; the passphrase is never resent on later submissions. This is a deliberate trade-off — the server sees the passphrase transiently at enroll and at login — documented in BLUEPRINT.md §03 Decision Log (2026-09). A returning applicant re-authenticates with the same passphrase via `POST /betat/login` (below) rather than re-enrolling.

**Option B — bring your own keypair (technical path, unchanged).** The private key never touches the server. Generate it yourself from any Python shell with `cryptography` installed:

```bash
python -c "
from betat_community.communityauth import crypto
private_key, public_key = crypto.generate_keypair()
signature = crypto.sign(private_key, public_key)   # self-sign the public key as proof of possession
print('public_key:', public_key)
print('signature: ', signature)
print('private_key (keep this secret — needed again to authenticate later):', private_key)
"
```

Use `public_key` and `signature` as the enroll fields above. Keep `private_key` — `authenticate()` calls (for future actions requiring re-proof) need it to sign a fresh message each time; it's never sent during enrollment itself.

## `POST /betat/login` — re-authenticate a passphrase-based identity

Public. Only for `cryptographic_signature` identities enrolled via Option A above (a passphrase) — identities enrolled by pasting a manual `public_key`/`signature` have nothing to re-derive and get no benefit from this endpoint. Re-derives the keypair from the passphrase and compares the public key against what was recorded at enrollment; returns the same token issued then.

```bash
curl -X POST https://your-community.example/betat/login \
  -H "Content-Type: application/json" \
  -d '{"identity": "did:key:z6MkfExample", "passphrase": "your passphrase"}'
```

```json
{
  "identity": "did:key:z6MkfExample",
  "identity_type": "cryptographic_key",
  "authentication_method": "cryptographic_signature",
  "display_name": "Ada Lovelace",
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

`401` with `{"error": {"code": "invalid_credentials", ...}}` for a wrong identity or passphrase — deliberately the same error either way, so a failed guess can't reveal whether an identity exists.

## Two-phase peer-vouch enrollment

`community_peer_vouching` no longer accepts a `vouchers` list from the applicant — that used to trust whoever the applicant *named*, with no confirmation those people had actually agreed. Enrolling now opens a pending request and returns **202**, not 201:

```json
{
  "status": "pending_vouches",
  "request_id": 4,
  "vouch_count": 0,
  "vouches_needed": 2,
  "message": "Enrollment request received. 2 existing enrolled members must vouch for you..."
}
```

## `POST /betat/vouch/{request_id}` — vouch for a pending peer-vouch request

Requires a Provenancier token — the vouch is attributed to whoever is actually authenticated, not merely named by the applicant. Idempotent (vouching twice does nothing extra) and rejects vouching for your own request.

```bash
curl -X POST https://your-community.example/betat/vouch/4 \
  -H "Authorization: Token <voucher-token>"
```

Returns the same `pending_vouches`/200 shape as above while below threshold, or the enroll-style `identity`/`token`/201 shape once the last required vouch lands and the applicant is promoted to a full Provenancier.

## `POST /betat/submit` — submit a contribution

Requires a Provenancier token. Content is never uploaded — only where it lives and its hash.

```bash
curl -X POST https://your-community.example/betat/submit \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Field observation — Lake Oku, June 2026",
    "location": "https://archive.example/obs-4471",
    "content_hash": "sha256:e3b1c74d02a8f5e9b6d0c3a7f42e18d5b9c6a0f3e7d2b8c4a1f6e0d9b3c7a5f2",
    "language": "en",
    "declaration_accepted": true
  }'
```

```json
{
  "id": 12,
  "provenancier_identity": "did:key:z6MkfExample",
  "title": "Field observation — Lake Oku, June 2026",
  "location": "https://archive.example/obs-4471",
  "content_hash": "sha256:e3b1c74d02a8f5e9b6d0c3a7f42e18d5b9c6a0f3e7d2b8c4a1f6e0d9b3c7a5f2",
  "language": "en",
  "declaration_accepted": true,
  "status": "pending_review",
  "submitted_at": "2026-09-01T12:00:00Z",
  "reviewed_at": null,
  "reviewed_by": "",
  "rejection_reason": "",
  "record_id": ""
}
```

`declaration_accepted` must be `true` or the submission is refused outright (400), not stored pending.

## `GET /betat/queue` — pending submissions

Requires a verifier token (a staff account — see the framework's admin panel). Returns every submission with `status: "pending_review"`, same shape as above.

## `POST /betat/review/{id}` — accept or reject

Requires a verifier token. Accept builds a full PROVENANCE_SPEC record and appends it to the store; reject closes the submission with no record.

```bash
curl -X POST https://your-community.example/betat/review/12 \
  -H "Authorization: Token <verifier-token>" \
  -H "Content-Type: application/json" \
  -d '{"decision": "accept"}'
```

The response is the submission again, now with `status: "accepted"` and `record_id` populated — fetch that id at `/betat/records/{id}` (below) to see the full record.

## `GET /betat/info` — community identity

Public, no auth.

```bash
curl https://your-community.example/betat/info
```

```json
{
  "id": "marinebiology-lagos.org",
  "name": "Marine Biology Lagos",
  "domain": "marine biology",
  "content_type": "scientific_observation",
  "hi_standard": "human-originated, community-verified",
  "auth_methods": ["community_peer_vouching", "cryptographic_signature"],
  "store_uri": "https://marinebiology-lagos.org/betat/records"
}
```

404 with `{"error": {"code": "not_configured", ...}}` before `betat init` has run.

## `GET /betat/records` — paginated, newest first

Public. `?hi_only=true` filters to `hi_tag: true` records (currently all of them — the store rejects anything else at write time); `?since=<timestamp>` also works here, though `/changes` below is the dedicated endpoint for that.

```bash
curl "https://your-community.example/betat/records?page=1"
```

```json
{
  "count": 42,
  "next": "https://your-community.example/betat/records?page=2",
  "previous": null,
  "results": [ /* full PROVENANCE_SPEC records — see PROVENANCE_SPEC.md */ ]
}
```

## `GET /betat/records/{id}` — one record

Public. Returns the record exactly as stored (matches `PROVENANCE_SPEC.md`'s Record Format), or 404 `not_found`.

```bash
curl https://your-community.example/betat/records/7c4a1d29e8f3b6a5d0c2f47e91b8a3d6c5e2f0a9b7d4c1e8f6a3b0d7c4e1f8a2
```

A conforming client always recomputes this record's hash and compares it to `record_id` before trusting it — see [RENDERING.md](RENDERING.md)'s integrity states; the bundled UI does exactly this on every record it renders.

## `GET /betat/changes?since=` — incremental feed

Public. Same shape as `/records`, filtered to records after the given ISO 8601 timestamp — built for crawlers polling on a schedule.

```bash
curl "https://your-community.example/betat/changes?since=2026-08-01T00:00:00Z"
```
