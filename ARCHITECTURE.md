---
title: Architecture
parent: For Builders
nav_order: 1
---

# Betat — Architecture

> This document is for **Contributors** — developers and technologists building the Betat open-source codebase.
> If you are a **Provenancier** — a human being who wants to record or archive human-originated content — start with [README.md](README.md) and [WHAT_IS_BETAT.md](WHAT_IS_BETAT.md).
> For the philosophy underneath every decision here, read [WHY_BETAT.md](WHY_BETAT.md).

---

## Terminology

**Provenancier** *(pro-VEN-an-see-ay)* — a verified human being who records, archives, or submits human-originated content to a Betat community. The subject of every provenance record.

**Contributor** — a developer or technologist who builds, improves, or extends the Betat open-source codebase. Participates via GitHub.

---

## The Core Reframing: Betat Is a Protocol, Not a Datastore

Betat does not attempt to store the world's human content. A system that tried to would require infrastructure budgets in the millions and would concentrate control in whoever paid for it — both fatal to the mission.

Instead, **Betat defines protocols**: open specifications that let independent parties store and serve their own content in an interoperable way. Each community stores its own records at its own host. Betat defines the shared language they all speak.

This is how the systems that actually reached worldwide scale began. The web did not scale because one organization stored every page — it scaled because open protocols (HTTP, HTML, URLs) let anyone publish and anyone find. Betat applies the same lesson to human provenance.

> *Guiding principle: Human-originated content, verified by community, tagged as HI, preserved with provenance, and accessible without barriers.*

Every architectural decision is tested against that principle and against the philosophy in WHY_BETAT.md: **prove the real, don't chase the fake.**

---

## The Three Protocols

The technical core of Betat is three open protocols. Everything else — the registry, the indexes, the community framework — is an implementation of these.

### 1. The Provenance Protocol
The record format: what data must accompany every verified human contribution, how records are hashed for tamper-detection, and how corrections and disputes are appended. The seed of this protocol already exists as [PROVENANCE_SPEC.md](PROVENANCE_SPEC.md).

### 2. The Community Protocol
How a community operates: how it authenticates its Provenanciers, how it verifies human origin under its own declared standard, and how it produces valid provenance records. The reference implementation of this protocol is the **community framework** — see [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md).

### 3. The Federation Protocol
How independent stores expose their records to the world: a small set of open, read-only endpoints that any registry, crawler, or index can call to discover and read a community's published provenance records. Federation is what makes independently hosted communities into one findable whole.

A minimal federation surface (to be refined by Contributors):

```
GET /betat/info            → community identity, declared HI standard, protocol version
GET /betat/records         → paginated list of provenance records (newest first)
GET /betat/records/{id}    → a single provenance record
GET /betat/changes?since=  → records added since a given timestamp (for incremental crawling)
```

All endpoints are public and unauthenticated — reading is always free. All responses are provenance records or metadata, never hosted content: the records point to content at its own location.

---

## betat main: A DNS-Like Registry, Not a Central Index

The role of betat.org (betat main) is deliberately narrow. It does **not** host communities, store content, or hold the world's hi_tags. It serves a few purposes only:

**1. Host the canonical protocols.** The specifications live at betat main as the reference every implementation conforms to — the way W3C hosts web standards.

**2. Run the registry.** A lightweight, DNS-like directory of known communities and stores: for each, its name, its host address, its declared content domain, and its declared HI standard. The registry holds **pointers, not content** — the way DNS tells a browser where a domain lives without hosting that domain's pages.

**3. Run the reference index — the bootstrap guarantee.** Because every community publishes its records via the open federation protocol, anyone can crawl the registered stores and build a search index. betat main runs one such index as a public convenience and, **for the seed era, commits to crawling every registered community** — so registration alone guarantees a community appears in at least one public index from day one, and no early community publishes into a void. This costs little: the crawler reads pointers and small JSON records, never hosted content.

The crawler that powers this reference index is **betat main's own local component, implemented and hosted in betat main's codebase — it is not part of the `pip install betat-community` package**. Communities never implement, run, or receive a crawler; their entire discoverability duty is serving the federation endpoints (which the seed framework does automatically) and registering once. Crawlers come to them, the way search engines come to websites.

betat main's index remains *an* index, never *the* index: multiple independent indexes can and should coexist, exactly as multiple search engines crawl the same web, and nothing in the protocol privileges betat main's crawler over anyone else's.

### Registry interface sketch

```
GET  /registry/communities            → list of registered communities (name, host, domain, standard)
GET  /registry/communities/{id}       → one community's registration record
POST /registry/register               → register a community (authenticated; verified organization)
```

Registration is where community identity is verified: the registry confirms the community controls the domain that is its ID, via a DNS TXT challenge (roadmap — see COMMUNITY_FRAMEWORK.md, Community Identity).

### Why this dissolves the centralization problem
A central hi_tag index would be a single point of failure and control — whoever ran it could be pressured, captured, or simply go offline, taking discoverability with it. A registry of pointers is different in kind: it is cheap to run, trivial to mirror, and replaceable. If betat main disappeared, the communities, their records, and any independent indexes would continue to exist and function; only one convenient directory would need re-mirroring. Discovery degrades gracefully instead of dying centrally.

---

## How Discovery Works, End to End

1. A community stands up a store (using the community framework or its own conforming implementation) and registers its pointer with the registry.
2. Indexes — betat main's or anyone's — read the registry, crawl each store's federation endpoints, and build searchable indexes of provenance records. **Pull is the primary model; a push fallback exists** for constrained hosts: a community may ping the registry ("I have new records — crawl me now") or, where even that fails, submit a signed records export by any means available (see COMMUNITY_FRAMEWORK.md, `betat announce` / `betat export`).
3. A reader searches any index, filters for verified human content (`hi_only`), and follows each record's content location to the work itself.
4. A tag-on-render tool (a browser extension, for example) queries an index for the page being viewed and displays HI badges on content with matching provenance records. Content without a record is shown as **unverified — never "fake."**

No step requires betat main to exist, except the convenience of its registry — which can be mirrored.

---

## The HI Tag and Declared Standards

The line Betat draws is **authentic origin versus fabricated reality** — not human-hands versus machine-hands (see WHY_BETAT.md). AI used as a tool aiding authentic human work can carry honest provenance; AI used to fabricate reality and pass it off as real can never be certified.

Because different domains legitimately draw the tool/fabrication line differently, **Betat does not impose one global definition of "human-created."** What every community does operate above is the **Betat Baseline** — the process-integrity floor (verified human, review recorded, declaration signed, standard declared truthfully) that may be strengthened but never weakened; see [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md), The Betat Baseline. Above that floor:

- Each community **declares its standard explicitly** — e.g., *human-authored, AI-untouched* or *human-conceived, AI-assisted production*.
- That declaration is carried **inside every provenance record** the community issues.
- A future reader therefore sees not a bare "HI" but *"HI, under this community's stated standard."*

The hi_tag is a truthful, qualified statement of provenance — not a binary that hides its own assumptions. What Betat forbids is not the tool; it is the **false claim**.

---

## Access Model

| Action | Authentication required |
|--------|------------------------|
| Read the registry, any index, any record | No — always public |
| Crawl a store's federation endpoints | No — always public |
| Submit a contribution as Provenancier | Yes — verified community member |
| Register a community with the registry | Yes — verified organization or body |
| Contribute code as Contributor | GitHub account — standard open source |

Reading is always free. Writing provenance is always earned. This is the project's contract with the future.

---

## Seed Technology Stack

The stack below is a recommended starting point for reference implementations — **not a constraint**. Any component may be replaced by community consensus with whatever scales better or fits the purpose better. The protocols are what must remain consistent; the technology beneath them is always open to change.

| Piece | Technology | Rationale |
|-------|-----------|-----------|
| Registry & reference index | Python / Django; SQLite at install, PostgreSQL in production | Widely known; zero-config first run, robust engine for deployment |
| Community framework | Python package (see COMMUNITY_FRAMEWORK.md) | Install-and-run, Django-style |
| Federation endpoints | Plain HTTPS + JSON | Universal; no special client needed |
| Record integrity | SHA-256 content addressing | Already in PROVENANCE_SPEC.md |
| Tag-on-render client | JavaScript / Web Extensions API | Cross-browser standard |
| Hosting (seed) | Single Linux VPS per party | Each party hosts its own; no central cost |

---

## Open Problems, Named Honestly

Two hard problems remain open. The protocol approach makes them smaller and later — not solved. Contributors are invited to work on both.

**1. Registry concentration.** Even a pointer-only registry is a mild concentration point. DNS shows this is manageable (quasi-central, yet the web is robust), and the registry is designed to be mirrorable — but a truly federated or distributed registry design is future work.

**2. Cross-community trust.** The community model handles trust *within* a community (members know the domain and each other). It does not yet solve trust *between strangers across communities*: how does a reader trust that a community they have never heard of genuinely verified humans rather than rubber-stamping fabrication? Declared standards in every record help (the claim is at least explicit and auditable), but reputation, auditing, or attestation mechanisms between communities remain an open design space.

Naming these openly is deliberate. A seed that pretends its hard problems are solved invites the wrong kind of trust. A seed that states them precisely invites the right kind of Contributor.

---

## What To Build First

1. **The community framework reference implementation** — see [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md). One genuinely working community proves the whole model.
2. **The registry** — a small Django app implementing the registry interface above.
3. **A reference crawler + index** — reads the registry, crawls federation endpoints, serves search with an `hi_only` filter.
4. **A browser extension** — the first tag-on-render client.
5. **Improvements to the protocols and these documents** — via issues and pull requests.

---

*Protocols: [PROVENANCE_SPEC.md](PROVENANCE_SPEC.md) · Framework: [COMMUNITY_FRAMEWORK.md](COMMUNITY_FRAMEWORK.md) · Philosophy: [WHY_BETAT.md](WHY_BETAT.md) · Overview: [README.md](README.md)*
