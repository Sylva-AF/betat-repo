---
title: Rendering the Record
parent: For Builders
nav_order: 4
---

# Betat — Rendering the Record

> Status: guidance (seed) · Open for Contributor review
> The Integrity States section is **binding for the bundled UI** — adopted into COMMUNITY_FRAMEWORK.md, Consumption Model, Layer 2.
>
> One provenance record, worn three ways: the developer's JSON, the reader's result card, and the inspectable evidence behind it. This document shows all three, so anyone building on Betat can preview what is actually being built — and so every UI renders the record honestly.

---

## The Principle

The provenance record is the single object. Everything a human ever sees is a **rendering** of it — never something beside it, never something instead of it.

This is structurally guaranteed, not merely hoped: the bundled UI (and any well-built frontend) consumes the public JSON API only, so every human-facing view is by definition composed from record fields. The card is the courtesy; the record is the evidence. Both are always available, to everyone, without an account.

---

## Presentation 1 — What the Machine Sees

The record as developers, crawlers, and indexes receive it (a dummy example; hashes are illustrative — see the note at the end):

```json
{
  "betat_version": "0.1",
  "record_id": "7c4a1d29e8f3b6a5d0c2f47e91b8a3d6c5e2f0a9b7d4c1e8f6a3b0d7c4e1f8a2",
  "timestamp": "2026-09-14T16:42:07Z",
  "hi_tag": true,

  "provenancier": {
    "identity": "bhc-provenancier-0047",
    "identity_type": "peer_attested",
    "authentication_method": "community_peer_vouching",
    "display_name": "Ma'a Ngwe Tchoumi"
  },

  "content": {
    "type": "oral_knowledge",
    "title": "How the dry-season planting songs were taught in Bafang, as I learned them from my grandmother (audio, 34 min, with transcript)",
    "location": "https://archive.bamileke-heritage.org/recordings/2026/planting-songs-bafang-0047.html",
    "content_hash": "sha256:e3b1c74d02a8f5e9b6d0c3a7f42e18d5b9c6a0f3e7d2b8c4a1f6e0d9b3c7a5f2",
    "language": "bbj"
  },

  "community": {
    "id": "oral-history.bamileke-heritage.org",
    "name": "Bamileke Heritage Oral History Community",
    "domain": "Oral tradition and cultural memory of the Bamileke people",
    "content_type": "oral_knowledge",
    "store_uri": "https://oral-history.bamileke-heritage.org/betat/records"
  },

  "verification": {
    "method": "community_peer_review",
    "verified_by": "oral-history.bamileke-heritage.org",
    "verification_timestamp": "2026-09-16T09:15:33Z"
  },

  "declaration": {
    "text": "I declare that this content was originated by a human being. I am that human being, or I am an authorized representative of that human being. I understand that this declaration is permanent, public, and append-only — it cannot be removed or modified.",
    "language": "en",
    "custom_addition": "Declared HI standard: human-originated, community-verified; recorded live by two community members and transcribed by hand. Recorded with the speaker's consent for permanent public archiving."
  },

  "record_signature": ""
}
```

---

## Presentation 2 — What the Reader Sees

The same record, rendered as a search-result card:

```
┌────────────────────────────────────────────────────────────────────┐
│ [HI]  How the dry-season planting songs were taught in Bafang,     │
│       as I learned them from my grandmother (audio, 34 min,        │
│       with transcript)                                             │
│                                                                    │
│ Oral knowledge · in Ghomálá' · by Ma'a Ngwe Tchoumi                │
│ Verified by the Bamileke Heritage Oral History Community           │
│   — peer review, Sept 16, 2026                                     │
│ Standard: human-originated, community-verified                     │
│ Recorded Sept 14, 2026                                             │
│                                                                    │
│ Listen at the source ↗        View full provenance record          │
└────────────────────────────────────────────────────────────────────┘
```

### Field-by-field: how the record becomes the card

| Record field | Rendered as |
|---|---|
| `hi_tag: true` | The visible **HI** badge (the label "HI" is required for cross-platform recognition) |
| `content.title` | The card's headline |
| `content.type` | "Oral knowledge" — plain words, not the enum value |
| `content.language: "bbj"` | "in Ghomálá'" — the human name of the language |
| `provenancier.display_name` | "by Ma'a Ngwe Tchoumi" (pseudonymous names render the same way) |
| `community.name` + `verification.method` + `verification_timestamp` | The verification sentence, in prose |
| declared standard (in `declaration.custom_addition`) | **Always shown.** The reader sees *HI under a stated standard*, never a bare HI |
| `timestamp` | "Recorded Sept 14, 2026" |
| `content.location` | "Listen at the source ↗" — the UI links to the work; it never hosts it |
| the whole record | "View full provenance record" — see Presentation 3 |

### What stays behind the card — but does silent work

`record_id`, `content_hash`, `betat_version`, `store_uri`, and identity internals do not clutter the card. They are not decoration, though: they power the integrity states below and the evidence view. Machine fields are hidden from the glance, never from the inspection.

---

## Presentation 3 — The Evidence, One Click Away

"View full provenance record" opens the raw record (Presentation 1), readable by anyone, no account required. This bridge is not optional in a well-built UI. It is the project's trust model in miniature:

> **Trust the badge, or inspect the certificate yourself — both are always available.**

A UI that showed the card but hid the record would be asking for faith. Betat asks only for reading.

---

## Integrity States — the Rendering Rule That Matters Most

The record carries two tripwires, and rendering them honestly is where a UI earns its keep.

**The content tripwire.** `content_hash` is the SHA-256 of the content at the moment of verification. A good UI (and any index) re-checks it when it can, and renders one of three states:

| State | Condition | What the reader sees |
|---|---|---|
| **Verified match** | Content at `location` hashes to `content_hash` | The normal card; optionally a quiet "content verified intact" |
| **Changed since verification** | Content reachable but hash no longer matches | A visible flag: *"The content at this location has changed since it was verified on Sept 16, 2026. What you are seeing may differ from what the community verified."* The HI badge refers to the verified original — the UI must not present the current content as the verified one. |
| **Source unreachable** | `location` cannot be fetched | *"The original location is not currently reachable. The provenance record remains valid and intact."* — the record outlives the link; unreachable is not revoked. |

**The record tripwire.** `record_id` is the hash of the record itself. A conforming client validates it on read; a record that fails is rendered as **tampered** — never silently shown as valid.

Two honesty rules bind every state: a hash mismatch is reported as *changed*, never as *fake* — the record proves what was verified then, not what happened to the file since. And absence of any record renders as **unverified**, with wording that never implies machine-made: *"No provenance record found — human origin not confirmed."* Unverified is an absence of proof, not an accusation.

---

## For the Seed Implementation

- The bundled UI (framework Consumption Model, Layer 2) renders exactly the card and evidence views above, deliberately plain.
- Hash re-checking may be periodic or on-view; the seed may ship it as a background task with a "last checked" note. What the seed must not do is display a mismatch state it has detected as a normal card.
- This dummy record makes a good first test fixture precisely because its illustrative hashes are wrong: a conforming store rejects it as-is and accepts it only after computing the real canonical hash — which is itself a test of `verify_integrity()`.

---

*Record format: [PROVENANCE_SPEC.md](PROVENANCE_SPEC.md) · System design: [ARCHITECTURE.md](ARCHITECTURE.md) · The UI's API contract: [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md), Consumption Model*
