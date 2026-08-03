---
title: Community Framework
parent: For Builders
nav_order: 2
---

# Betat — Community Framework Specification

> Version: 0.2 (seed) · Status: open for Contributor review
>
> This document specifies the **reference community framework**: the "Django for Betat." A Contributor installs it and gets a working, protocol-conforming Betat community out of the box — authentication, verification workflow, append-only provenance store, and federation endpoints. This is the piece that makes worldwide scale possible without central hosting: Betat does not host communities, it **equips people to host their own correctly**.
>
> Pseudocode and interface sketches below are design guidance, not final code. The reference implementation will refine them.
>
> **The framework is optional; the protocol is mandatory. A community's legitimacy derives from protocol conformance and registry verification, never from which software produced it.** Any implementation, in any language, that conforms to the protocols is a valid Betat community. This framework is the paved road, not the tollgate.

---

## Design Goals

1. **Works as-is.** A freshly installed community must genuinely function with zero further development: accept a member, verify a contribution, write a valid provenance record, publish it via federation. Even if never optimized, it is a working "community bucket."
2. **Interoperable by default.** Everything it publishes conforms to the provenance and federation protocols, so every new community is automatically discoverable and readable by any registry or index.
3. **Sovereign above the baseline.** The installing community governs its own membership, declares its own HI standard at or above the Betat baseline, and chooses its authentication from the protocol-approved list. The framework enforces protocol conformance and the baseline — never editorial policy.
4. **Boring technology, zero-friction first run.** The seed implementation targets Python on a single Linux host (though it runs anywhere Python runs). Exactly as Django does, a fresh install runs on **SQLite with zero configuration** — a working community exists minutes after `pip install` — while **PostgreSQL is the recommended engine for any real deployment**, with step-by-step setup documented as the "Recommended production stack" guide. All choices are replaceable by consensus.

---

## The Betat Baseline

Every community operates at or above the Betat baseline. The baseline governs **process integrity**, not creative method:

1. **Verified human.** Every provenance record is issued for a Provenancier authenticated by the community through at least one protocol-approved method, with the method recorded in the record.
2. **Review happened.** Every accepted record passed the community's verification workflow; the verifier identity and timestamp are recorded.
3. **Declaration signed.** The standard human-origin declaration was accepted at submission and travels permanently with the record.
4. **Standard declared truthfully.** The community's declared HI standard is carried in every record it issues. Issuing a record under a standard the work does not meet is a false claim — the one act the protocol exists to prevent — and is grounds for delisting from any registry.

Communities may **strengthen** the baseline: stricter content standards, stronger authentication, additional verifiers. No community may weaken, waive, or remove any element of it.

The baseline guarantees that every HI tag, from any community, means: *a real, verified human, honestly declared.* The declared standard then tells the reader *which kind* of human-made — from "human-conceived, AI-assisted production" to "human-authored, AI-untouched." The baseline deliberately does not regulate the level of AI assistance; that remains the community's declared position. The line Betat draws is authentic origin versus fabricated reality — per WHY_BETAT.md, the crime is the false claim, not the tool.

The default standard rendered at `betat init`, which communities may only build upward from:

```
hi_standard: "human-originated, community-verified"
```

---

## Community Identity

Every community carries a permanent ID, stamped into every provenance record it issues. The convention:

> **A community ID is a fully-qualified domain name the community controls at the moment of minting, written lowercase, exactly as it is.**

Examples: `indigenous-knowledge-society.ca` · `marinebiology-lagos.org` · one organization running two communities uses subdomains: `oral-history.ubc.ca`, `field-botany.ubc.ca`. The founding community's ID is `betat.org`.

Uniqueness is inherited from domain ownership — the domain industry already guarantees no two parties control the same name, so no central naming authority is needed and none exists. The ID is permanent: it is a birth certificate, not a live dependency. If the community later changes hosting, or even loses the domain, every record it ever issued remains valid — the registry entry (ID → current host), not the domain, says where the community lives now.

Domain control is **declared** at `betat init` and **verified** at registry registration (a DNS TXT challenge issued by the registry — see Roadmap). Verification lives at the registry because it is the one place it can be checked by anyone; the install ceremony can never be an identity authority, since anyone can run or modify open-source code.

---

## What an Operator Gets Out of the Box

```
$ pip install betat-community        # or: git clone betat-repo/framework
$ betat init my-community
  → name, community ID (domain), knowledge domain, content_type,
    HI standard (baseline rendered; strengthen-only),
    authentication method(s) from the protocol list   (guided setup)
$ betat runserver
  → seed website live on SQLite; federation endpoints live; admin panel live
```

### The post-install seed website

Mirroring Django's famous first-run page, a fresh install serves a **working seed website immediately** — running on SQLite, fully usable for evaluation and the acceptance test — with a visible **readiness checklist** of what remains before real deployment:

1. **Install a robust database engine** — PostgreSQL recommended; SQLite is for install verification and evaluation only.
2. **Set up your community's provenance assertions and records** — declare your HI standard properly (at or above the Betat baseline) and configure the record fields your domain requires.
3. **Initiate your chosen authentication method(s)** — select and configure deliberately from the protocol list; the shipped defaults are safe for evaluation use only.
4. **Adapt your own UI bundle if desired** — the bundled UI works as-is; replace or supplement it with Vue, React, or any client via the public API (see Consumption Model).

The checklist is not decorative: each item links to its documentation page, and the seed site displays which items are still outstanding — so an operator always knows the distance between "it runs" and "it is production-ready."

After `init`, the operator has:

- A **community configuration** (identity, domain, declared HI standard) — published at `/betat/info`
- An **authentication scaffold** for Provenanciers (pluggable methods, below)
- A **verification workflow** (submission → review → accept/reject)
- An **append-only provenance store** (writes valid PROVENANCE_SPEC records; no update/delete)
- **Federation endpoints** (public, read-only, per the federation protocol)
- An **admin panel** for the community's own verifiers and governance
- A **bundled minimal web UI** (see Consumption Model below) so the community works with zero frontend development

---

## How the Framework Is Consumed

The framework is **API-first, UI-optional**: headless by design, usable out of the box. It does not pick a winner among frontend technologies — it is consumable by all of them. Consumption happens in three layers:

### Layer 1 — The JSON API (the contract, mandatory)
Every capability of the framework — enroll, authenticate, submit, review, accept, list records — is exposed as a documented REST/JSON endpoint. This is the layer that React, Vue, Svelte, mobile apps, command-line tools, and any future client consume. It speaks the same language as the public federation surface (JSON over HTTPS), so internal and external consumers share one consistent contract.

Any UI wires to it the same way. The contract in six lines, from any client:

```javascript
// Read — public, no authentication (Foundational Guideline 1)
const records = await fetch("https://my-community.example/betat/records?hi_only=true")
  .then(r => r.json());

// Write — authenticated Provenancier only
await fetch("https://my-community.example/betat/submit", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${provenancierToken}`
  },
  body: JSON.stringify({
    content_type: "text",
    title: "Field observation — Lake Oku, June 2026",
    location: "https://archive.example/obs-4471",
    declaration_accepted: true
  })
});
```

The snippet teaches the access model: the read carries no credentials; the write does.

### Layer 2 — The bundled minimal UI (included, replaceable)
A plain, functional web interface ships with the framework so the seven-step acceptance test passes on a fresh install with **zero frontend work**: an enrollment page, a submission form, a verifier review queue, and a public records list. The seed implementation uses **Django templates** — server-rendered, no build step, no Node toolchain — so an operator on a bare Linux VPS has a working community from `pip install` alone. It is deliberately plain: its job is to work, not to impress.

**Mandatory rule: the bundled UI consumes the public JSON API only — no internal shortcuts.** If the bundled UI can do something the API cannot, the API is incomplete and external frontends become second-class. The bundled UI is the API's first consumer; this is what guarantees the contract stays complete.

**Rendering requirements (integrity states).** The bundled UI renders records per [RENDERING.md](RENDERING.md), and its integrity rules are binding, not optional: validate `record_id` on read and render a failing record as **tampered**, never silently as valid; render the content-hash states honestly — *verified match*, *changed since verification*, *source unreachable* — and never present content whose hash no longer matches as the verified content; always display the declared HI standard alongside the HI badge; always link the full provenance record (the evidence is one click away); and render absence of a record as **unverified**, with wording that never implies machine-made. A mismatch is reported as *changed*, never *fake* — the record proves what was verified then, not what happened to the file since. Custom frontends (Layer 3) are strongly urged to meet the same bar; a UI that hides the evidence or overstates a badge is asking readers for faith, and Betat asks only for reading.

### Layer 3 — Custom frontends (the extension path)
Because Layer 1 is complete, any community may replace or supplement the bundled UI with its own frontend — React, Vue, a mobile app — consuming the same API without touching the framework core. This is where a community-built ecosystem of themes and frontend starters can grow over time, exactly as Django's ecosystem grew around Django REST Framework. The framework provisions for every frontend not by shipping one, but by guaranteeing that **nothing requires the bundled UI**.

---

## Core Interfaces (sketches)

### Community configuration

```python
class CommunityConfig:
    id: str                  # FQDN the community controls at minting,
                             # e.g. "marinebiology-lagos.org"
    name: str
    domain: str              # knowledge domain governed
    content_type: str        # PROVENANCE_SPEC content type this community may verify
    hi_standard: str         # the community's DECLARED standard,
                             # at or above the Betat baseline, e.g.
                             # "human-authored, AI-untouched"
                             # "human-conceived, AI-assisted production"
    auth_methods: [AuthMethod]  # ≥1 from the protocol list, chosen at init
    store_uri: str           # where this community's records are published
```

The `hi_standard` declaration is written into **every provenance record** the community issues (see PROVENANCE_SPEC `declaration.custom_addition` / future dedicated field). This is how "HI under a stated standard" travels with the work.

### Authentication (pluggable, floored)

**Authentication floor.** Every community MUST implement at least one authentication method from the protocol-approved list. Communities MAY stack additional listed methods. No community may operate with no authentication, or substitute a method not on the list. The list is protocol-level: it changes only by community consensus, and methods may be added or deprecated-with-migration-path — never silently removed. The method used is recorded in every provenance record; stronger methods produce stronger credibility, and the record makes the strength visible to every reader.

The list offers varieties rather than a single gate, because different communities live under different constraints — a single mandated method would be a wall some communities get locked behind.

```python
class AuthMethod(Protocol):
    def enroll(self, applicant) -> ProvenancierIdentity | Rejection: ...
    def authenticate(self, credentials) -> ProvenancierIdentity | Rejection: ...

# Protocol list — seed implementations shipped:
#   PeerVouchAuth          — N existing members vouch for an applicant
#   CryptoKeyAuth          — applicant proves control of a signing key
#   InstitutionalAuth      — token/attestation from a trusted institution
# Protocol list — roadmap:
#   GovernmentIdAuth       — attestation against government-issued identity
#   BehavioralAuth         — human verification at moment of submission
# Method used is recorded in every record (provenancier.authentication_method).
```

### Submission and verification workflow

```python
def submit(content_ref, identity: ProvenancierIdentity, declaration) -> Submission:
    # content is NOT uploaded to the framework; content_ref is its
    # persistent location (URI/DOI/IPFS) + sha256 content_hash
    assert identity.is_authenticated
    return Submission(status="pending_review", ...)

def review(submission, verifier) -> Accepted | Rejected:
    # verifier applies the community's declared HI standard.
    # The framework enforces PROCESS (who may verify, that review happened);
    # the community supplies JUDGMENT (does this meet our standard?).
    ...

def accept(submission, verifier) -> ProvenanceRecord:
    record = build_record(          # per PROVENANCE_SPEC v0.1
        provenancier=submission.identity,
        content=submission.content_ref,
        community=config,
        verification=(method, verifier, now_utc()),
        declaration=standard_declaration + config.hi_standard,
        hi_tag=True,
    )
    record.record_id = sha256(canonical(record))
    store.append(record)            # append-only; no other write path exists
    return record
```

### Append-only store

```python
class ProvenanceStore:
    def append(self, record: ProvenanceRecord) -> RecordId: ...
    def get(self, record_id) -> ProvenanceRecord: ...
    def list(self, since=None, page=None) -> [ProvenanceRecord]: ...
    def verify_integrity(self, record_id) -> bool:   # recompute sha256, compare
    # Deliberately absent: update(), delete().
    # Corrections/disputes are NEW records referencing the original
    # (correction_of / disputes fields per PROVENANCE_SPEC).
```

Storage engines, stated honestly: on the **SQLite install default** (for testing, development, and getting familiar with the framework), SQLite has no database roles, so nothing below the framework's code fully prevents modification. The seed adds guard triggers that abort any UPDATE or DELETE as defense-in-depth, and the cryptographic hash chain makes any tampering detectable — but this remains weaker than role separation, which is precisely why the readiness checklist requires a real engine before deployment. On **PostgreSQL (the recommended production stack)**, the app role is granted INSERT-only privileges with UPDATE/DELETE revoked at the database-permission level — the operator's own database enforces append-only, not merely convention. PostgreSQL is not shipped with the seed; the documentation's step-by-step "Recommended production stack" guide covers installation, configuration, role setup, and the migration path from a SQLite store.

### Federation endpoints (served automatically)

```
GET /betat/info            → CommunityConfig (public identity + declared standard)
GET /betat/records         → paginated records, newest first
GET /betat/records/{id}    → one record
GET /betat/changes?since=  → incremental feed for crawlers
```

Public, unauthenticated, read-only, JSON. This is the community's face to every registry and index in the world.

### Discoverability commands: `announce` and `export`

Crawling assumes the community's host is reliably reachable — a fair assumption for a VPS, a poor one for intermittent or very cheap hosting, which matters given Betat's explicit reach into developing regions. The framework therefore ships two push-side commands as the accessibility valve (pull via crawling remains the primary model):

```
$ betat announce
  → pings the registry / reference index: "new records available — crawl me now"
    (may also run automatically when new records are accepted)

$ betat export
  → produces a signed, integrity-verifiable dump of this community's provenance
    records, submittable to any index by any means available when live
    crawling of the host is not practical
```

**What this framework deliberately does not include: a crawler.** Crawling is the job of index operators, not communities. betat main implements its own local crawler inside its registry/reference-index codebase — that crawler is not part of this package, and a community never needs one. A community's entire discoverability duty is: serve the federation endpoints (automatic), register once, and optionally `announce`.

---

## What the Framework Deliberately Does NOT Do

- **Host content.** Records point to content at its own persistent location; the framework stores provenance only.
- **Judge quality or truth of content.** It verifies human origin under the community's declared standard — nothing more.
- **Talk to betat main at runtime.** Registration with the registry is a one-time, explicit act by the operator. A community functions fully even if no registry exists.
- **Impose a content standard beyond the baseline.** Process integrity is guaranteed by the Betat baseline; the content standard is declared per community, at or above the baseline, and recorded per record — per WHY_BETAT.md, the crime is the false claim, not the tool.
- **Act as an identity authority.** `betat init` prepares a community; only registry verification confirms one. Running this framework grants no legitimacy that an independent implementation lacks.

---

## Minimal Working Community — Acceptance Test

A framework build is considered a valid seed release when this end-to-end scenario passes on a fresh install:

1. Operator runs `betat init` on a fresh SQLite install, mints a community ID (domain), and declares an HI standard at or above the Betat baseline.
2. A Provenancier enrolls via a configured protocol-list auth method.
3. The Provenancier submits a text contribution (content hosted elsewhere, hash provided).
4. A verifier reviews and accepts it.
5. A valid PROVENANCE_SPEC v0.1 record with `hi_tag: true` and the declared standard appears in the store.
6. `GET /betat/records` returns it; `verify_integrity` passes; no API or DB path exists to modify or delete it.
7. An independent crawler, given only the community's host address, discovers and reads the record.

Seven steps. If they pass, the model is proven — one working community bucket, extensible by the next Contributor.

---

## Documentation Standard: A Snippet for Every Capability

The framework's documentation follows the style that makes libraries like **django-mptt** easy to adopt (see its overview documentation as the reference model): a single, browsable documentation site — readthedocs-style — where **every public capability of the framework is shown with a copyable usage snippet**, not just described in prose.

Concretely, this means:

- Every API endpoint, every framework function, and every CLI command has its own documented example: the call, its inputs, and its real output.
- An operator or Contributor should be able to learn the entire framework by reading the docs top to bottom and running the snippets — installation, `betat init`, enrolling a Provenancier, submitting, reviewing, reading federation endpoints, replacing the UI.
- The readiness-checklist items on the seed website link directly into these pages, so "what do I do next" always has a documented answer with example code.

**Definition of done includes documentation:** a capability without a usage snippet is not finished. Pull requests adding or changing public behavior must update the corresponding documentation page. This rule exists because the framework's promise — that any developer can extend it — is only true if every functionality is learnable from a snippet.

---

## Roadmap Beyond Seed (for Contributors)

- Additional auth plugins per the protocol list (government-ID attestation, behavioral attestation)
- Registry-side domain-control verification at registration (DNS TXT challenge)
- Multi-verifier quorum review; verifier rotation
- IPFS-backed content addressing option for `content.location`
- Automatic announce-on-accept refinement and mirrored-registry support
- Cross-community attestation experiments (toward the open trust problem — see ARCHITECTURE.md, Open Problems)

---

## Changelog

- **0.2** — Merged the latest 0.1 revision (post-install seed website with readiness checklist, `announce`/`export` discoverability commands, no-crawler rule, documentation standard) with the adopted amendments: the Betat Baseline (process-integrity floor, strengthen-only); authentication floor (at least one method from the protocol-level list); community ID convention (forward FQDN controlled at minting; registry TXT verification on roadmap); SQLite ships with seed for testing/dev, PostgreSQL documented as the "Recommended production stack"; framework-optional/protocol-mandatory principle; Layer 1 API consumption example; bundled-UI rendering and integrity-state requirements (see RENDERING.md).
- **0.1** — Initial seed specification.

---

*Protocols: [PROVENANCE_SPEC.md](PROVENANCE_SPEC.md) · System design: [ARCHITECTURE.md](ARCHITECTURE.md) · Rendering: [RENDERING.md](RENDERING.md) · Philosophy: [WHY_BETAT.md](WHY_BETAT.md)*
