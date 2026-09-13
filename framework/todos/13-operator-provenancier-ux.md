# TODO 13 — Operator & Provenancier UX: admin dashboard, adaptive access, passphrase visibility

> Status: done (all six tasks implemented and test-confirmed 2026-09-13 — 185 tests passed)
> Blueprint: no dedicated §13 section — landed as Decision Log entries under §03/§07 (the sections that actually changed), per this repo's "spec → blueprint → TODOs → code" authority rule. See BLUEPRINT.md's 2026-09-12/13 entries under those sections for full implementation detail.
> Spec reference: COMMUNITY_FRAMEWORK.md → "Consumption Model, Layer 2"; "Authentication (pluggable, floored)"
> Depends on: 03, 04, 07 · Was blocking: the v0.1 ship gate — now cleared.

## Why this exists

During TODO 12's fresh-venv verification pass (2026-09-12), the developer walked the founding-phase peer-vouch flow end-to-end as a real, non-technical operator would: created a test community (`organicaf.org`, `community_peer_vouching` only), enrolled a first test Provenancier under a different identity than the admin account, and had to fall back to raw Django `/admin/` to approve it. Then tried the nav's "Log in" link to return as that Provenancier and hit a passphrase form that can never work for a peer-vouch identity (no passphrase exists for that method). The developer's own words: "not human friendly especially to public users non tech person" — flagged as a real gap to close before shipping, not a one-off confusion.

## Goal

Make the two points where a non-technical human actually touches authentication — **(a)** an operator approving new members, **(b)** a Provenancier returning to contribute again — self-explanatory inside the bundled UI, with no Django-admin knowledge and no guessing required. Adapt what's shown to what the community's configured `auth_methods` actually support, instead of one generic flow that only works for some of them.

## Tasks

- [x] **Operator dashboard, in bundledui, staff-gated.** Done and test-confirmed 2026-09-13 (80
  passed) — see Session progress below. A new page (e.g. `/community/admin`, or grow `/community/queue` into a dashboard with two sections) listing pending `PeerVouchRequest`s (founding and normal, with vouch progress) alongside pending `Submission`s, with one-click actions:
  - Founding requests: a single "Approve" button calling the same `PeerVouchAuth.promote()` logic `communityauth/admin.py`'s `approve_founding_requests` action already uses — no Django admin needed for this at all.
  - Normal (non-founding) requests: read-only vouch-count display. These promote automatically via `POST /betat/vouch/{id}` from *other Provenanciers*, not staff — don't add a staff override button that bypasses the peer-vouch trust model.
  - Reuse the existing `_verifier_token()`/`is_staff` gate (`views.py`) `bundledui-queue` already uses — no new auth mechanism.
  - **Nav entry point (scoped 2026-09-12):** `base.html`'s nav today has exactly one account CTA (the "Log in"/"Log out" link at lines 50–60), and it reflects only the *Provenancier* session (`request.session.provenancier_token`) — there is no staff-awareness in the nav at all (Review queue is always visible; it just redirects to verifier-login if the visitor isn't staff). Add a separate, staff-gated ("`{% if request.user.is_staff %}`") "Admin" dropdown next to — not merged into — the existing Provenancier CTA, since the two are different auth systems in this codebase and conflating them would blur that. Build it with the same pure-CSS checkbox-hack toggle `.bt-help` already uses for tooltips (`betat.css` lines 389–443) — no JS needed, this interaction (open/close on click) doesn't need real functional JS the way the passphrase-visibility toggle (task 4 below) does. Contents: "Approve enrollments" (this task's dashboard) and, once task 5 below lands, "Change password."
- [x] **Adaptive access entry point** (done 2026-09-12, tests passed — see Session progress below), replacing the unconditional "Log in with your passphrase" page:
  - Read the community's configured `auth_methods` (via `/betat/info`, same call `enroll_view` already makes) and show only what's actually possible.
  - If `cryptographic_signature` (passphrase-capable) is enabled: show the existing passphrase form.
  - If the *only* enabled method(s) are `community_peer_vouching`/`institutional_endorsement` (no passphrase concept): don't present a passphrase field that will always fail. Show honest guidance instead — e.g. "This community's enrollment doesn't use a password. Return to the device/browser you enrolled from, or ask an administrator for help."
  - If multiple methods are enabled, some passphrase-capable and some not: resolve identity first (a plain "Identity" field, submitted alone), then reveal only the field(s) relevant to *that* identity's actual method.
  - Implements the general principle raised this session directly: expose only what a given auth method needs, never a one-size-fits-all form.
- [x] **Real self-service token retrieval** for peer-vouch/institutional identities (done and test-confirmed 2026-09-13) — replaces today's "hope it's the same browser session" reliance and the "ask an admin to read the Token out of `/admin/`" workaround for applicants who opt in. Security design decided with the developer first: an **optional, applicant-chosen claim passphrase** (not a server-generated token), **optional not required** at enroll. Full implementation detail in BLUEPRINT §03's 2026-09-13 Decision Log entry: `PeerVouchRequest.claim_passphrase_hash`, `POST /betat/enroll/claim`, `EnrollForm` fields, `/community/claim` page, `provenancier_login.html` guidance now links there. **Confirmed: migration applied, full suite green — 175 passed (including `test_acceptance.py`).**
- [x] **Passphrase visibility toggle — DECIDED 2026-09-13: no JS in v0.1, no toggle ships.** Developer's call, resolving the open JS-vs-no-JS question above. A real reveal-on-click toggle is impossible in pure CSS regardless of the checkbox-hack technique — CSS cannot mutate an `<input>`'s `type` attribute, and there is no CSS-only way to mirror a password field's live value into a visible decoy field either (that mirroring itself requires JS to read the input event). So "CSS-only decoy field" was never actually a viable middle option once examined closely — the real choice was "add the first functional JS in the community-facing UI" vs. "ship nothing here." Decided: nothing, for v0.1. **What already covers the underlying risk:** `enroll.html`'s existing `passphrase`/`passphrase_confirm` double-entry (`forms.py` `EnrollForm`) catches the most common failure mode — typing two *different* things — with a clear "Passphrases do not match" error before submission. It does not catch typing the *same* wrong thing twice (a consistent typo, or simply forgetting the passphrase immediately after choosing it), which a visual reveal would have caught; that residual gap is accepted for v0.1 and is a natural roadmap item once the passphrase-rotation task below (or a broader client-side crypto pass, see BLUEPRINT §03's 2026-09 Decision Log "move derivation into the browser" roadmap note) makes revisiting the no-JS stance worthwhile anyway. `provenancier_login.html`'s single passphrase field is unchanged and needs no matching double-entry — a mistyped *login* passphrase fails cleanly (`invalid_credentials`) and is safely retryable, unlike a mistyped *enroll* passphrase, which could create an identity keyed to a passphrase the applicant doesn't actually know.
- [x] **Verifier password change link** (scoped 2026-09-12, done and test-confirmed 2026-09-13). Added `<a href="{% url 'admin:password_change' %}">Change password</a>` to the Admin dropdown in `base.html`, right after "Approve enrollments." No new view, no new logic — purely wires up Django's existing stock view. Confirmed: 3 passed.
- [x] **Provenancier passphrase rotation** (scoped 2026-09-12, done and test-confirmed 2026-09-13). Security design decided with the developer first: proof of ownership is the *current* passphrase (not an active session token) — same trust model as `/betat/login`; the DRF token always rotates too (a stolen token is a separate secret from the passphrase, so leaving it stable would make "rotate after suspected compromise" cosmetic). Verified before coding, not assumed: `build_record()` never references `verification_material['public_key']` — it copies identity/type/method/display_name as a frozen snapshot at accept time — so the "what happens to old records" concern in this task's original text was a non-issue by construction. New `POST /betat/rotate-passphrase`, new `/community/rotate-passphrase` page linked from the login page's passphrase-available branch. Full detail in BLUEPRINT §03's 2026-09-13 Decision Log entry (the one right after task 3's). No model changes, no migration needed. **Confirmed: full suite green, 185 passed.**

## Acceptance criteria

- [x] An operator can approve a founding-member (or read vouch progress on a normal) enrollment request entirely inside the bundled UI, without visiting `/admin/`. (Confirmed 2026-09-13: 80 tests passed, including all 12 new.)
- [x] A Provenancier enrolled via any currently-shipped auth method has a discoverable, correctly-labeled way to resume contributing — never a passphrase form for a method that has no passphrase. (Confirmed 2026-09-12: 3 tests passed.)
- [x] Passphrase fields let a user verify what they typed before submitting a value that can never be recovered if mistyped — met for v0.1 by `enroll.html`'s existing `passphrase`/`passphrase_confirm` double-entry (catches mismatched typos); a full visual-reveal toggle was decided against for v0.1 (no JS), see Tasks above. `provenancier_login.html` needs no equivalent — a mistyped login passphrase is safely retryable, not unrecoverable.
- [x] None of the above requires Django-admin knowledge or "same browser session" folklore to operate correctly — for applicants who set a claim passphrase; those who don't keep the honest, unchanged "same session / ask an admin" fallback, which was always this file's accepted scope for opt-outs.
- [x] A verifier can reach Django's password-change flow from inside the bundled UI, not just by guessing `/admin/password_change/` exists. (Confirmed 2026-09-13: 3 tests passed.)
- [x] A Provenancier who enrolled via passphrase can rotate it after proving they hold the current one, without any way for someone who only knows their identity string to do the same. (Confirmed 2026-09-13: 185 tests passed.)

## Security notes

- The self-service claim/status endpoint (task 3) — **addressed and test-confirmed 2026-09-13**: `POST /betat/enroll/claim` requires a separate claim passphrase only the applicant knows (hashed, never stored plaintext), not a bare identity-string lookup.
- The operator dashboard's approve action must remain staff-only (the same gate `bundledui-queue` already uses) — never expose an unauthenticated approve path.
- ~~Any real JS added for the passphrase toggle must not log, store, or transmit the passphrase anywhere it doesn't already go~~ — moot: decided against shipping any passphrase-toggle JS in v0.1 (see Tasks above).
- Passphrase rotation — **addressed and test-confirmed 2026-09-13**: `POST /betat/rotate-passphrase` verifies proof of the *current* passphrase before accepting a new one, same "no bare identity-string" standard as the claim endpoint; the passphrase is never logged or stored anywhere beyond the existing transient enroll/login exposure already accepted in the §03 2026-09 Decision Log.

## Out of scope

- Changing what the underlying auth plugins actually require (identity/vouch/passphrase mechanics) — this is presentation/UX only, not §03's authentication logic.
- A full multi-method "log in" system with sessions/refresh tokens — out of scope for the seed; this is about making the *existing* mechanics discoverable, not adding new session infrastructure.

## Session context — investigated 2026-09-12, confirmed not assumed

- `provenancier_login.html` (lines 23–26): a single hardcoded `<input type="password" name="passphrase">`, no toggle of any kind.
- `enroll.html` (lines 104–113) / `forms.py` (lines 39–45): `EnrollForm.passphrase`/`passphrase_confirm` are Django `PasswordInput` widgets — same gap.
- No bundledui route/view/template anywhere touches `PeerVouchRequest` for staff review — confirmed absent from `urls.py`, `views.py`, and `queue.html`. The only staff-facing approval path today is `communityauth/admin.py`'s `PeerVouchRequestAdmin` + `approve_founding_requests` action, i.e. raw Django admin.
- `landing_view`/`landing.html` is an unauthenticated first-run readiness checklist with no staff concept at all — a new admin dashboard needs its own staff-gated route, not an extension of `landing`, which would conflate anonymous first-run visitors with authenticated staff.
- The pure-CSS "checkbox hack" toggle already used for `.bt-help` tooltips (`betat.css` lines 389–443) is real and reusable for some interactions, but cannot flip an `<input>`'s `type` attribute — a genuine passphrase-visibility toggle needs actual JS.

Deliberately not fixed live during the walkthrough that surfaced it — the self-service claim endpoint's security model and the JS-vs-no-JS tradeoff for the visibility toggle are real design decisions that deserve their own scoped pass, not reactive coding mid-walkthrough. This file exists so the next session picks this up with full context instead of re-discovering it.

## Session progress — 2026-09-12, implementation started, ended mid-task-1

Investigated one more fact before coding (via a read-only agent) that matters for task 2 (adaptive
access): `CryptoKeyLoginView` (`communityauth/api/views.py:89-138`, backs `POST /betat/login`) has
**no gating against `CommunityConfig.auth_methods` at all** — unlike `EnrollView`, which explicitly
rejects a disabled method. It queries `Provenancier.objects.get(identity=..., authentication_method=
CryptoKeyAuth.method_name)`, so a wrong-method identity (e.g. peer-vouched) safely falls through to
the same generic `invalid_credentials` 401 as a nonexistent identity — no information leak, no crash,
but also no way to tell the two cases apart server-side. Not fixed this session (would be an API-level
correctness change, separate from this TODO's UI scope) — flagged here so it isn't rediscovered from
scratch, and worth a follow-up task if this file gets picked up again.

**Task 1 (adaptive access entry point) — done, not yet test-run:**
- `bundledui/views.py`'s `provenancier_login_view` computes both `passphrase_login_available`
  (`'cryptographic_signature' in auth_methods`) and `other_methods_enabled`
  (`bool(set(auth_methods) - {'cryptographic_signature'})`), passing both into the template context.
- `provenancier_login.html` now branches on `passphrase_login_available`: shows the existing
  passphrase form when true (with an added note when `other_methods_enabled` is also true — the
  "multiple methods" middle case, resolved as "show the form plus a note" per the task's own
  suggestion, not "resolve identity first" — simpler and sufficient since crypto-signature identities
  can always use this form regardless of what else is enabled); shows an honest "this community's
  enrollment doesn't use a password" `bt-banner-neutral` guidance block when false, with no form at all.
- Added three tests to `tests/test_bundledui.py` (new "provenancier login, adaptive access" section,
  just above the peer-vouch section): form-shown/no-note when only `cryptographic_signature` is
  enabled, form-hidden/guidance-shown when only `community_peer_vouching` is enabled, and
  form-shown/note-present when both are enabled.
- **Not yet run** — this session cannot execute `pytest` (Bash is sandbox-blocked here); the developer
  needs to run `pytest tests/test_bundledui.py -k provenancier_login` before trusting this is correct.

**Next session, in order:**
1. Developer: run the three new tests above; fix forward if any fail (untested-by-execution code). ✅
   Done — 3 passed, confirmed by the developer.
2. Task 2 (staff-gated enrollment dashboard) and task 3 (self-service claim token) are still fully
   unstarted. Task 3 needs its security design decided *before* any code, per the Security notes above.
3. Task #4 (passphrase visibility toggle) is blocked on a JS-vs-no-JS decision from the developer —
   see the Tasks section above; do not implement either option without that decision.

**Scoping session, 2026-09-12 (same day, after task 1 landed):** developer asked how the operator
dashboard should be wired into the nav, and whether any credential-update logic exists today.
Answered by reading `base.html` and `communityauth/api/views.py` directly rather than assuming —
confirmed the nav has no staff-awareness at all today, and confirmed there is no change-password or
change-passphrase endpoint anywhere in the codebase. Two new tasks added above as a result (verifier
password-change link, Provenancier passphrase rotation), plus a nav-wiring sub-bullet on task 1
(staff-gated "Admin" dropdown, separate from the Provenancier login/logout CTA, built with the
existing pure-CSS checkbox-hack toggle). **Scoped only — no code written for any of this yet;** next
session should still start with task 2 (the dashboard itself, including its new nav dropdown), since
the two new tasks depend on that dropdown existing (password-change link) or are independently
scheduled security-design work (passphrase rotation).

**Task "operator dashboard" — done, not yet test-run (2026-09-13):** implemented per the scoping
above. New API: `GET /betat/vouch-requests` + `POST /betat/vouch-requests/{id}/approve`
(`communityauth/api/views.py`), both `IsVerifier`-gated. New bundledui: `admin_dashboard_view` +
`approve_founding_request_view` (`ApiClient`-only, no ORM), `admin_dashboard.html`, routes
`/community/admin` + `/community/admin/approve/<id>`. Nav: staff-gated "Admin ▾" dropdown in
`base.html`, pure CSS (`betat.css`'s new `.bt-nav-dropdown*` rules), no JS. Side effect: `IsVerifier`
moved from `workflow/api/mixins.py` to `common/permissions.py` (now used by two apps); the old file is
a removal-note stub, `git rm` it whenever convenient. Full detail in BLUEPRINT §03/§07's 2026-09-13
Decision Log entry. Tests added to `test_communityauth.py` (6 new) and `test_bundledui.py` (6 new,
covering dashboard gating/listing/approve plus nav dropdown show/hide). **Confirmed 2026-09-13: full
suite green, 80 passed** (`tests/test_communityauth.py` + `tests/test_bundledui.py`).

**Remaining in this file:** the verifier password-change link and Provenancier passphrase-rotation
tasks (scoped above, not started); the self-service claim endpoint (needs its security design decided
first); the passphrase visibility toggle (needs the developer's JS-vs-no-JS call first).
