# ROADMAP.md — Betat Community Framework

> This file tracks post-v0.1 phases for the framework build (`framework/`), distinct from the
> UI's own internal "Phase 1/2/3" terminology used in `todos/07-bundled-ui.md` (installer →
> configured community UI → setup wizard) — those are states of a single install; the phases
> below are features layered on top of a shipped v0.1.

## v0.1 (seed) — shipped

Everything in [TODO.md](TODO.md) sections 01–12: a single sovereign community, pluggable
authentication (crypto key, institutional endorsement, peer vouching with founding-phase
bootstrap), the submission/verification workflow, the append-only provenance store, federation
endpoints, the bundled minimal UI (installer, setup wizard, community pages), the post-install
seed website, and discoverability (`announce`/`export`).

---

## Phase 2 — Timeline tree and backfill mechanism

**What it is:** a public-facing visualization of the global effort to
establish provenance for existing human-originated content created before
communities began recording at creation time. The timeline maps discovered
content across a year-indexed interface. Public visitors browse and read.
Enrolled Provenanciers assert or flag. Community verifiers promote confirmed
content to permanent Betat records.

**Why it exists:** content created before widespread Betat adoption has
no provenance record. The backfill mechanism addresses this retroactively.
It has a natural lifecycle — it runs intensively at launch, narrows as
adoption grows, and eventually becomes a background process as new content
is recorded at creation time rather than discovered retroactively.

**The decay curve:**
```
Launch          → backfill runs intensively, timeline grows rapidly
Adoption grows  → new content recorded at creation, gap narrows
Maturity        → backfill runs as background process, catching stragglers
Full adoption   → backfill deprecated, its job is done
```

### The timeline tree (public UI)

The timeline is a public page on every community's bundled UI — no
enrollment required to browse. It loads the minimum viable data on first
visit (under 10KB) and lazy-loads additional data as the user drills down.
Designed for mobile users on constrained connections first.

**Lazy loading by decade:**
```
[1991–2000]  [2001–2010]  [2011–2020]  [2021–now]

Tap a decade → loads decade summary (~2KB)
Tap a year   → loads year breakdown (~3KB)
Tap a type   → loads first 10 nodes (~5KB)
              → [Load 10 more] for additional nodes
```

The internet as a global phenomenon began in 1991 (World Wide Web
public launch). The timeline starts there. Content predating widespread
internet use is out of scope for the automated backfill agent — oral
histories and pre-digital materials enter through direct community
submission by Provenanciers with personal knowledge of the content.

**Visibility layers:**
```
Anonymous public    → browse timeline, read node metadata, see counts
                      cannot assert or flag
Enrolled            → assert human origin, flag as fake/AI-generated
Provenancier        → assertions carry verified identity weight
Community verifier  → promote confirmed nodes to permanent records
                      reject nodes, mark as disputed
```

The assert/flag buttons are visible to anonymous visitors but inactive.
Clicking either triggers the enrollment prompt — the timeline is the
enrollment conversion surface. A visitor who finds content they have
personal knowledge about has an immediate, specific reason to enroll.

**The enrollment trigger:**
A visitor who clicks Assert or Flag sees:
```
To assert on this content you need to be a verified member
of a Betat community. Your identity gives your assertion weight.

[Browse communities]  [Start a community]
```

Enrollment is the door to participation, not a prerequisite to reading.

### The backfill agent

A Django management command that the community administrator runs
deliberately — never automatic. Consequential actions are human
decisions; the agent runs at the operator's direction.

**Starting:**
```bash
betat backfill start \
  --scope scientific_observation \
  --year-from 2010 \
  --year-to 2023 \
  --rate-limit 100   # requests per minute
```

**Stopping:**
```bash
betat backfill stop
# Releases all open claims — other communities can pick them up
# No work is lost
```

**Agent phases (cycling until stopped):**
1. Discover — query public APIs for content matching community scope
2. Check and claim — query coverage map, claim uncovered content
3. Prepare draft — fetch metadata only, never full content
4. Queue management — pace submissions to community's verification capacity

**Sources queried (public APIs only, rate-limited):**
- CrossRef (academic papers with DOIs)
- Zenodo (research data and preprints)
- Internet Archive (web pages, audio, video)
- PubMed (biomedical literature)
- DOAJ (open access journals)

The agent never fetches full articles. It caches metadata only:
title, author, publication date, URL, content hash, source, confidence.
Under 500 bytes per node. The full article is never touched unless
a user deliberately clicks through to the source URL.

**Automatic stop conditions:**
- All content in scope is claimed, complete, or flagged
- Coverage map unreachable for more than 24 hours (releases claims)
- Pending queue reaches community maximum (pauses until verifiers catch up)

**Crawl cadence:**
One complete pass per quarter is the recommended baseline. The agent
writes progress to a local state file and resumes from where it left
off if interrupted. Between passes the cache is static — users see
the state from the last crawl, not a live count. This is honest and
appropriate: the timeline is a map of what has been discovered, not
a live feed.

### The metadata cache

**Storage: GitHub Pages (free, global CDN)**

The agent writes metadata to JSON files organized by decade and content
type. GitHub Pages serves them as static assets — no database needed
for the cache layer, zero infrastructure cost, CDN distribution built in.

```
/timeline-cache/
  1991-2000/
    summary.json              ← decade totals (< 1KB)
    scientific_observation.json
    creative_work.json
    oral_knowledge.json
  2001-2010/
    summary.json
    ...
```

The agent commits updated JSON files to the repo on each pass.
GitHub Actions deploys automatically. The cache is always consistent
with the last completed crawl.

**Cache payload (per node, ~500 bytes):**
```json
{
  "url": "https://doi.org/10.xxxx/...",
  "content_hash": "sha256:3f7a...",
  "title": "Field observations on coral bleaching",
  "author": "Dr. Jane Osei",
  "original_creation_date": "2019-03-14",
  "original_creation_date_precision": "day",
  "source": "zenodo.org",
  "content_type": "scientific_observation",
  "confidence": "high",
  "assertion_count": 3,
  "flag_count": 0,
  "status": "pending_confirmation",
  "cached_at": "2026-09-10"
}
```

### Agent conflict resolution — the coverage map

Multiple communities running backfill agents simultaneously must not
duplicate work. The coverage map at betat.org coordinates all agents.

**Hash states:**
```
open      → no agent has claimed this content
claimed   → an agent is working on it (with timestamp and community id)
complete  → a permanent record exists (with record id)
```

**The claim-and-report pattern:**
```
Agent discovers content hash H
    ↓
Query coverage map: what is H's status?
    ↓ open              ↓ claimed           ↓ complete
Claim H             Check claim age        Skip
Prepare submission  If expired → re-claim  Link to existing record
Record created      If fresh → skip
Report complete
```

Claims expire after 72 hours. An agent that goes offline automatically
releases its claims. No manual intervention needed.

**Coverage map federation endpoints (new in Phase 2):**
```
GET  /betat/backfill/coverage          → paginated hash status list
POST /betat/backfill/claim             → claim a hash
POST /betat/backfill/complete          → report a hash recorded
GET  /betat/backfill/status/<hash>     → single hash status query
```

**Coverage map ownership:**
betat.org hosts the global coverage map in Phase 2. Long-term the
architecture moves toward distributed ownership — communities sync
directly with each other rather than through a central coordinator.
This follows the same decentralization trajectory as the registry itself.
The centralized start is a practical choice, not a permanent constraint.

### BackfillDraft — the confirmation queue

Discovered content enters a BackfillDraft queue, separate from the
normal Submission queue. A BackfillDraft requires a minimum number of
Provenancier assertions before it becomes a full Submission.

```
BackfillDraft states:
  pending_assertions  → waiting for Provenanciers to assert
  confirmed           → threshold met, promoted to Submission
  flagged             → majority flagged as fake, rejected
  expired             → no action after timeout, claim released
```

The default assertion threshold is 2 — configurable per community.
A BackfillDraft that reaches the threshold enters the community's
normal verifier review queue as a standard Submission.

### What must exist before Phase 2 starts

- At least one real community running v0.1 with real Provenanciers
- Real records in the store (the timeline needs content to point to)
- The PROVENANCE_SPEC optional fields committed (`original_creation_date`) — **done, v0.1**
- The Timeline nav tab placeholder deployed — **done, v0.1**

Phase 2 does not begin until these conditions are met. A timeline tree
with no records and no Provenanciers to assert is an empty page that
harms adoption rather than helps it.

### What this phase adds to existing architecture

**New:** backfill agent management command, coverage map API endpoints,
BackfillDraft model, timeline tree UI, metadata cache structure.

**Unchanged:** provenance store, enrollment flow, submission flow,
verifier review queue, federation records API, bundled UI community
pages, betat.css. The backfill mechanism builds on top of what exists.

*The timeline tree is not a permanent feature — it is a transitional
tool that does its job and becomes unnecessary. When the gap between
existing content and recorded content closes, the backfill mechanism
is deprecated. That is the correct outcome.*

---

## Phase 2 — Cross-community network features

**What it is:** the features that turn a collection of independent
communities into a connected network. Individual communities can run
and produce records without these features — they are v0.1. But
the network effects that make Betat valuable at scale require communities
to know about each other, trust each other deliberately, and enable
Provenanciers to participate across communities.

### Cross-community enrollment (recognition requests)

A Provenancier enrolled in Community A who wants to join Community B
submits a recognition request rather than starting enrollment from scratch.

**The request carries:**
- Source community id and display name (who they are in Community A)
- Source enrollment token (proof of existing verification)
- Reason for joining Community B

**Community B's admin reviews:**
- Is Community A a community we recognize?
- Does this person's profile fit our scope?

**On approval:** Community B issues its own token. The Provenancier
holds separate tokens per community. Memberships are independent —
records in Community A stay under Community A's verification; records
in Community B stay under Community B's. The person's cross-community
membership is their own business and is not published by default.

**The enrollment path type:** `cross_community` — a new variant of
the existing `pending_admin` enrollment state, with source community
context shown to the admin. Source token is verified against the source
community's federation API before submission.

**Why this matters for the timeline tree:** a Provenancier enrolled in
any community can assert on any community's timeline tree. Their assertion
carries their enrolled community's identity. A person enrolled in the
Calgary EV Technicians community can assert on a node in the West African
Oral History community's timeline — their identity travels with their
assertion, giving it weight that anonymous clicks cannot have.

### Provenancier-to-operator path (community founding)

Already works in v0.1 — `betat init` is independent of any existing
community. Phase 2 adds two improvements:

**Cross-community enrollment for founders:**
The person who starts Community C can submit a recognition request to
Community A (their source community). Community A recognizes their
verified identity. Community C's admin (themselves) approves the request.
They are now enrolled in Community C with their Community A verification
as context — faster than the founding-phase admin approval path, and
more meaningful because it carries their existing verification history.

**Registry network graph:**
When Community C registers, it optionally declares:
```json
"founded_by_provenancier_from": "community-a.org"
```

The registry builds a network graph from these declarations. The graph
shows which communities are generative — whose members go on to start
new communities. This is informational only; it carries no governance
relationship. Community A has no authority over Community C.

### Community trust declarations (registry feature)

Communities can optionally declare trust relationships with other
communities. A trust declaration means: "we accept cross-community
recognition requests from verified members of this community, subject
to our own admin review."

```json
"trusted_communities": [
  "community-a.org",
  "community-b.org"
]
```

This is not automatic access — it means Community B's admin will
look favorably on recognition requests from Community A members.
The admin still reviews and approves each request individually.
Trust declarations are public metadata in the registry.

Two communities that declare mutual trust can process recognition
requests quickly — the admin review is a light check rather than
a full evaluation. Two communities with no declared relationship
require a fuller evaluation before recognition is granted.

Trust declarations evolve over time as communities learn about
each other through the network. They are never required — every
community can choose to remain fully independent and evaluate
every recognition request from scratch.

### The network topology this produces

```
betat.org registry
    │
    ├── Community A (technology, Calgary)
    │   trusted_by: [Community B, Community C]
    │   founded: 2026
    │   Provenanciers: 47
    │   Records: 312
    │   Spawned: Community C
    │
    ├── Community B (oral history, West Africa)
    │   trusted_by: []
    │   founded: 2026
    │   Provenanciers: 23
    │   Records: 891
    │   Recognition requests received: 8 (from Community A: 3)
    │
    └── Community C (EV technicians, Canada)
        founded_by: community-a.org
        founded: 2027
        Provenanciers: 12
        Records: 67
        Spawned: [Community D (EV technicians, UK)]
```

This is a living network — not designed top-down but grown organically
from encounters, enrollments, and the decisions of real people to
extend their participation. The registry makes the growth visible.

### What Phase 2 requires before starting

- Multiple communities running v0.1 successfully
- Real Provenanciers who have expressed interest in joining other
  communities (the recognition request path has no point without demand)
- The registry updated to accept community metadata (trust declarations,
  founded_by field)
- The cross-community enrollment path designed and reviewed — it is new
  API surface with security implications (verifying source tokens against
  external community APIs requires careful design)

Phase 2 network features follow the timeline/backfill features, not
precede them. The timeline tree is what creates the cross-community
encounter — a Provenancier from Community A asserting on Community B's
timeline is the natural trigger for a recognition request. Build the
trigger before the response mechanism.

---

*Build plan: [TODO.md](TODO.md) · Design detail: [BLUEPRINT.md](BLUEPRINT.md) · Session bootstrap: [CLAUDE.md](CLAUDE.md)*
