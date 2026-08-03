---
title: Provenance Spec
parent: For Builders
nav_order: 3
---

# Betat — Provenance Record Specification

> Version: 0.1 (seed)
> Status: Open for community review and improvement
>
> This document defines the minimum data structure every verified human contribution to Betat must carry. It is intentionally minimal. Future versions may extend it. No version may remove a field defined here without a migration path and community consensus.

---

## Terminology

**Provenancier** *(pro-VEN-an-see-ay)* — a verified human being who records, archives, or submits human-originated content to a Betat community. The subject of every provenance record. When this specification refers to the person whose content is being recorded, it always means the Provenancier.

**Contributor** — a developer or technologist who builds or improves the Betat open-source codebase. A Contributor never appears in a provenance record. If you are reading this document to implement the spec, you are a Contributor.

These two roles may be held by the same person, but they are always described separately. The provenance record is about the Provenancier. The codebase is built by Contributors.

---

## Purpose

A provenance record answers the questions a future archivist must ask about any piece of human-originated content:

- **Who** made this? *(the Provenancier)*
- **When** was it made?
- **Where** does the content live?
- **Which community** accepted and verified it?
- **How** was the Provenancier authenticated?
- **How** was human origin verified?
- **Is** this tagged as Human Intelligence?
- **Is** the record intact and unmodified?

Every field in this specification exists to answer one of those questions.

---

## The HI Tag

The HI tag — `"hi_tag": true` — is the most important field in the provenance record. It is the signal that a verified Provenancier made this contribution, under a community standard, with their authentication on record.

Every valid Betat provenance record carries `"hi_tag": true`. A record without this field, or with `"hi_tag": false`, is not a valid Betat provenance record and must not be accepted by a conforming provenance store.

The HI tag in the record is the machine-readable foundation for the visible HI badge displayed in any interface built on Betat.

---

## Record Format

Provenance records are expressed in JSON. The format is open, human-readable, and implementable in any language or environment.

```json
{
  "betat_version": "0.1",
  "record_id": "<sha256 hash of canonical record content>",
  "timestamp": "<ISO 8601 UTC datetime of record creation>",
  "hi_tag": true,

  "provenancier": {
    "identity": "<community-defined identifier for the Provenancier>",
    "identity_type": "<see Identity Types below>",
    "authentication_method": "<see Authentication Methods below>",
    "display_name": "<optional human-readable name, may be pseudonymous>"
  },

  "content": {
    "type": "<see Content Types below>",
    "title": "<optional title or short description>",
    "location": "<URI, DOI, IPFS hash, or other persistent locator>",
    "content_hash": "<sha256 hash of the content at time of submission>",
    "language": "<ISO 639-1 language code>"
  },

  "community": {
    "id": "<unique community identifier>",
    "name": "<human-readable community name>",
    "domain": "<the knowledge domain this community governs>",
    "content_type": "<the content type this community is authorised to verify>",
    "store_uri": "<URI of the provenance store that holds this record>"
  },

  "verification": {
    "method": "<see Verification Methods below>",
    "verified_by": "<identity of verifier — may be community id for peer attestation>",
    "verification_timestamp": "<ISO 8601 UTC datetime of verification>"
  },

  "declaration": {
    "text": "I declare that this content was originated by a human being. I am that human being, or I am an authorized representative of that human being. I understand that this declaration is permanent, public, and append-only — it cannot be removed or modified.",
    "language": "<ISO 639-1 language code of declaration>",
    "custom_addition": "<optional community-specific addition to the declaration>"
  },

  "record_signature": "<optional cryptographic signature of record content by Provenancier>"
}
```

---

## Field Definitions

### `betat_version`
The version of this specification the record conforms to. Required. Enables future migration without breaking existing records.

### `record_id`
A SHA-256 hash of the canonical record content (full record JSON with `record_id` and `record_signature` set to `""` before hashing, keys sorted alphabetically, no whitespace). Required. Tampering produces a different hash and is immediately detectable.

### `timestamp`
ISO 8601 UTC datetime of when the provenance record was created. Required.

### `hi_tag`
Always `true` for valid Betat records. Required. The machine-readable Human Intelligence signal. This field is what the index queries when a UI requests the HI status of a piece of content. A record without `"hi_tag": true` is not a valid Betat provenance record.

### `provenancier.identity`
A community-defined identifier for the Provenancier. Required. The form depends on the community's authentication method — a cryptographic public key, an institutional ID, a peer-attested pseudonymous handle, or a verified government identity.

### `provenancier.identity_type`
The type of identifier used. Required. See Identity Types.

### `provenancier.authentication_method`
How the Provenancier was authenticated before being permitted to submit content. Required. See Authentication Methods. This records the gate the Provenancier passed — separate from how human origin of the content was subsequently verified.

### `provenancier.display_name`
Optional human-readable name. Pseudonymous submission is permitted — what matters is that the community has verified a human being behind the identity.

### `content.type`
The type of human contribution. Required. See Content Types. This field connects the submission to the community responsible for verifying it.

### `content.location`
A persistent locator for the content itself. Required. Betat does not host content — it points to it. Use the most permanent locator available: DOI for academic work, IPFS hash for decentralized storage, stable URI for institutional archives.

### `content.content_hash`
SHA-256 hash of the content at the time of submission. Required. If the content changes at its location, the hash will no longer match — alerting future readers that what they are reading may differ from what was originally verified.

### `community.id`
The community's permanent, globally unique identifier. Required. Convention: a fully-qualified domain name the community controls at the moment of minting, written lowercase (see COMMUNITY_FRAMEWORK.md, Community Identity). The ID is a birth certificate, not a live dependency — it never changes, even if the community later changes hosting.

### `community.content_type`
The content type this community is authorised to verify. Required. A community registered to verify `scientific_observation` cannot issue HI provenance records for `creative_work`. Communities are sovereign within their registered domain only.

### `verification.method`
How human origin was verified for this submission. Required. See Verification Methods. Distinct from authentication — authentication confirms the Provenancier is a known, verified human; verification confirms the content was originated by that human.

### `declaration.text`
The standard human origin declaration. Required. The default text is provided in this spec. Note that the declaration explicitly states the append-only and permanent nature of the record — the Provenancier acknowledges this at the moment of submission. Communities may add a `custom_addition` for domain-specific declarations.

### `record_signature`
Optional cryptographic signature of the record by the Provenancier. Strongly recommended where the identity type supports it. Provides non-repudiation — the Provenancier cannot later deny having made the submission.

---

## Identity Types

| Value | Description |
|-------|-------------|
| `cryptographic_key` | Provenancier identified by a public key; submissions signed |
| `institutional_id` | Provenancier verified by an institution |
| `government_id` | Provenancier verified against government-issued identity |
| `peer_attested` | Provenancier known to the community; attested by peers |
| `pseudonymous_peer_attested` | Pseudonymous; human origin attested by known community members |

---

## Authentication Methods

| Value | Description |
|-------|-------------|
| `cryptographic_signature` | Provenancier signs submissions with a verified key |
| `institutional_endorsement` | Institution endorses the Provenancier |
| `government_id_verification` | Provenancier verified against government ID |
| `community_peer_vouching` | Community members vouch for the Provenancier's identity |
| `behavioral_attestation` | Human verification at moment of submission |

---

## Verification Methods

| Value | Description |
|-------|-------------|
| `community_peer_review` | Community members reviewed and accepted the submission |
| `institutional_endorsement` | A trusted institution endorses the submission |
| `cryptographic_signature` | Provenancier signed the submission with a verified key |
| `editorial_review` | A designated community editor reviewed and accepted |
| `self_declared_authenticated` | Authenticated Provenancier self-declares human origin |

Note: `self_declared_authenticated` is only valid when the Provenancier has already passed community authentication. Self-declaration without prior authentication is not a valid Betat verification method.

---

## Content Types

| Value | Description |
|-------|-------------|
| `text` | Written text: article, essay, account, commentary, testimony |
| `scientific_observation` | A recorded scientific observation or dataset |
| `creative_work` | Art, music, literature, craft, or other creative output |
| `oral_knowledge` | Transcribed or recorded oral tradition, story, or teaching |
| `personal_testimony` | First-person account of a lived experience |
| `indigenous_knowledge` | Knowledge held and submitted by an indigenous community |
| `religious_text` | Religious commentary, teaching, or primary text |
| `legal_record` | Legal document, judgment, or formal record |
| `historical_record` | Historical document or account |
| `other` | Any human-originated content not covered above |

---

## Corrections and Disputes

Records are never modified or deleted. Corrections and disputes are new records.

**A correction** is a new provenance record with the same `content.type` as the original, carrying the corrected content, and including a `correction_of` field referencing the original `record_id`. The correction is itself a fully verified HI submission by a Provenancier.

**A dispute** is a new provenance record with `content.type` set to `text`, describing the nature of the dispute, and including a `disputes` field referencing the disputed `record_id`. The index surfaces disputes alongside the disputed record.

This preserves the complete human record — including its errors, revisions, and arguments. All of it is human. All of it belongs.

---

## Example Record

```json
{
  "betat_version": "0.1",
  "record_id": "a3f8c2d1e4b7...",
  "timestamp": "2026-06-12T14:32:00Z",
  "hi_tag": true,

  "provenancier": {
    "identity": "did:key:z6Mkf...",
    "identity_type": "cryptographic_key",
    "authentication_method": "cryptographic_signature",
    "display_name": "Ateafac Forsong"
  },

  "content": {
    "type": "text",
    "title": "Betat Provenance Specification — seed document",
    "location": "ipfs://bafybeig...",
    "content_hash": "sha256:9f4a2b...",
    "language": "en"
  },

  "community": {
    "id": "betat.org",
    "name": "Betat Founding Community",
    "domain": "Open Human Knowledge Infrastructure",
    "content_type": "text",
    "store_uri": "https://betat.org/store"
  },

  "verification": {
    "method": "cryptographic_signature",
    "verified_by": "did:key:z6Mkf...",
    "verification_timestamp": "2026-06-12T14:32:01Z"
  },

  "declaration": {
    "text": "I declare that this content was originated by a human being. I am that human being, or I am an authorized representative of that human being. I understand that this declaration is permanent, public, and append-only — it cannot be removed or modified.",
    "language": "en",
    "custom_addition": "This record is the founding provenance specification of Betat, submitted by its originator."
  },

  "record_signature": "base64:MEUCIQDx..."
}
```

---

## Versioning

This specification is version 0.1 — a seed. Future versions are developed by the Contributor community through the standard GitHub issue and pull request process.

**Rules for future versions:**
- Fields may be added in minor versions (0.2, 0.3...)
- Fields may never be removed without a major version bump and a migration path
- Breaking changes require community consensus
- The `betat_version` field ensures old records remain valid under new versions
- The `hi_tag` field is permanent and may never be removed or made optional
- The `provenancier` field name is permanent — it is the defining term of this project

---

## Implementation Notes

- Records stored and transmitted as UTF-8 encoded JSON
- Canonical form for hashing: `record_id` and `record_signature` set to `""`, keys sorted alphabetically, no whitespace
- Implementations must validate `record_id` on read to detect tampering
- Implementations must reject any record where `hi_tag` is not `true`
- Content is never stored in the provenance record — only its location and hash
- Provenance stores must be append-only — no delete or update operations on accepted records
- The seed stack (Python, Django, PostgreSQL) is a recommended starting point — Contributors are free to implement in any language or framework that conforms to this spec

---

*Read [ARCHITECTURE.md](ARCHITECTURE.md) for the system design.*
*Read [README.md](README.md) for the project's purpose and invitation.*
