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

`applicant` fields differ per method: `community_peer_vouching` needs `identity` + `vouchers` (existing members' identities); `cryptographic_signature` needs `public_key` + a self-signed `signature` (proof of possession — sign your own public key); `institutional_endorsement` needs `institution_id` + the institution's `signature` over your identity.

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
