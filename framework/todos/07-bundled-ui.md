# TODO 07 — Bundled Minimal UI

> Status: done — full test suite green on both SQLite (79/79) and PostgreSQL (77 passed + 2 expected skips)
> Blueprint: [§7](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Consumption Model, Layer 2" · [RENDERING.md](../RENDERING.md)
> Depends on: 03, 04, 06 · Blocks: 08

## Goal
The `bundledui` app: a plain, server-rendered UI so a fresh install is usable with zero frontend work — enroll, submit, review queue, public records list + detail — consuming the public API only.

## Tasks
- [x] Django templates (no build step, no Node): enroll, submit, review-queue, records-list, record-detail
- [x] All data via the public JSON API — no ORM shortcuts
- [x] Render per RENDERING.md card + evidence views
- [x] Integrity states (BINDING): validate `record_id` → tampered state; content-hash → verified / changed / unreachable; always show declared standard beside HI badge; always link full record; absence → unverified (never "fake")

## Acceptance criteria
- [x] four views work on a fresh install, zero frontend work
- [x] each view's data comes through the API (provable) — see "How API-only actually works" below
- [x] tampered / changed / unreachable fixtures each render the correct state
- [x] evidence ("view full record") link resolves to raw JSON

## Security notes
- No credentials or tokens rendered into templates or logs
- A detected mismatch must never render as a normal card

## Out of scope
- The first-run readiness page (§08)
- Any non-bundled frontend (Layer 3, community's own)

## Session handoff

### Design decisions (full rationale in BLUEPRINT §07 Decision Log)
- **CSS: one hand-written stylesheet, zero third-party/CDN code.** Matches "deliberately plain" and the project's low-bandwidth-operator concern (COMMUNITY_FRAMEWORK.md discoverability section). Color roles are driven by RENDERING.md's own honesty rules, not aesthetics: HI badge is a constant brand color (never reused for state signaling); verified is quiet/subdued (expected default); changed is amber (never red — "changed, never fake"); unreachable and unverified/absent are both neutral gray (never alarming); tampered is the *only* red/danger state (the one case actually proven bad).
- **How "API-only" actually works:** `bundledui/api_client.py`'s `ApiClient` wraps Django's `test.Client` — same URLconf/serializers/permission classes any external caller hits, no ORM shortcut, but no real socket back to its own process either (avoids same-process deadlock risk and a new HTTP-client dependency). Important correctness detail: `Client()` defaults to `Host: testserver`, which only passes `ALLOWED_HOSTS` in pytest's test-environment setup — every view constructs `ApiClient(server_name=request.get_host())` so the internal call reuses whatever host the browser's own request already passed validation for, in dev and production alike.
- **Session as "login."** Provenanciers have unusable passwords by §03 design (token-only) — so there's no username/password to log back in with. The enroll token is stored server-side in `request.session` after a successful enroll; that session *is* logged-in for this seed UI. **Known, honest gap:** no "log back in as an existing provenancier" flow exists — out of this section's scope, not silently solved.
- **Verifiers use real Django session login** (they have real passwords via `createsuperuser`/admin) — `bundledui/views.py`'s `_verifier_token()` then auto-provisions (`Token.objects.get_or_create`) a DRF token for the logged-in session on first use. This is the one direct ORM touch in the app — token bootstrapping for an already-authenticated user, not business logic (no `Submission`/`ProvenanceRecord`/`CommunityConfig` is ever touched directly).
- **`record_id` tampering is validated on every render** (cheap local recomputation via `common/hashing.py`, reused rather than reimplemented). **`content_hash` re-verification (fetch + hash `content.location`) only happens on the record-detail page**, not the list — RENDERING.md explicitly allows "periodic or on-view," and live-fetching every record's external content on every paginated list load would be slow and network-heavy for exactly the low-bandwidth operators this project cares about.
- **UI paths live under `/community/`** (not `/`) — avoids colliding with `/betat/` (the API) and doesn't claim the root path, which is §08's first-run landing page.

### Files written this section
- `bundledui/api_client.py`, `rendering.py`, `forms.py`, `views.py`, `urls.py`
- `bundledui/templates/bundledui/*.html` (base, enroll, submit, verifier_login, queue, records_list, record_detail, record_unverified, not_configured, `_record_card` partial)
- `bundledui/static/bundledui/style.css`
- `betat_community/urls.py` — mounts `community/` via `include()`
- `tests/test_bundledui.py` — new

### Closed out
Full suite green on both SQLite (79/79) and PostgreSQL (77 passed + 2 expected skips — the SQLite guard-trigger tests, correctly not applicable there). Confirmed working in a browser too (`/community/records`, `/community/enroll`, etc. — `/` itself is §08's landing page, added the same session). Section done.
