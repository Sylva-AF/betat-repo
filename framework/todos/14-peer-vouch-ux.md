# TODO 14 — Peer-vouch UX: click-to-vouch, targeted vouch requests, staff-scoped nav

> Status: done — migration applied, full suite green (132 passed), wheel build + install + manual
> UI verify signed off by the developer. Blueprint: no dedicated section —
> landed as Decision Log entries under
> §03/§07 (2026-09-20), per this repo's "spec → blueprint → TODOs → code" authority rule.
> Spec reference: COMMUNITY_FRAMEWORK.md → "Consumption Model, Layer 2"; "Authentication (pluggable, floored)".
> Depends on: 03, 04, 07, 13.

## Why this exists

Four bundled-UI gaps found in manual use of the shipped peer-vouch flow:

1. The *Enroll* nav CTA renders for an already-enrolled Provenancier, inviting pointless
   re-enrollment; `enroll_view` had no "already enrolled" guard.
2. The *Review queue* nav tab (a verifier tool) renders for every user, including normal
   Provenanciers who can only be bounced to a login they can't pass — noise and confusion.
3. `enroll_pending.html` showed the applicant a raw `/community/vouch/{id}` path to copy/paste —
   no clickable vouch CTA, and members had no in-UI way to discover pending requests.
4. `enroll.html` rendered the member list as a plain `<ul>` with no action — the applicant could
   not pick preferred vouchers, and a chosen voucher received no notification.

## Tasks

- [x] **Issue 1 — hide Enroll CTA when logged in.** `base.html`: gate the Enroll link on
  `{% if not request.session.provenancier_token %}`. `bundledui/views.py::enroll_view`: redirect a
  session that already holds `provenancier_token` to `bundledui-submit` (info message) so direct
  navigation is guarded too.
- [x] **Issue 2 — staff-scope Review queue + relocate verifier login.** `base.html`: gate the
  Review queue link on `{% if request.user.is_staff %}`. `provenancier_login.html`: add an
  always-shown "Are you a verifier? Sign in" link to `bundledui-verifier-login`. No view change —
  `queue_view` already redirects non-staff there.
- [x] **Issues 3 & 4 — targeted vouch requests.**
  - `communityauth/models.py`: `PeerVouchRequest.requested_vouchers` (JSONField, `default=list`).
    **Migration required — dev runs `makemigrations communityauth` + `migrate`.**
  - `plugins/peer_vouch.py::enroll()`: store `applicant['requested_vouchers']`, filtered to real
    enrolled identities, via `get_or_create` defaults.
  - `communityauth/api/views.py::OpenVouchRequestsView` (`IsAuthenticated`, resolves caller
    Provenancier, 403 `not_enrolled` otherwise) + `OpenVouchRequestSerializer` — pending
    non-founding requests, excluding own, with `vouch_count`/`vouches_needed`/`asked_me`/
    `already_vouched`. Wired at `GET /betat/vouch-requests/open` in `betat_community/urls.py`.
  - `bundledui`: `vouch_requests_view` + `community/vouch_requests.html` at
    `/community/vouch-requests` (name `bundledui-vouch-requests`); *Vouch requests* nav link for
    logged-in Provenanciers; `enroll.html` checkbox picker (`name="requested_vouchers"`);
    `enroll_view` injects `request.POST.getlist('requested_vouchers')`; `enroll_pending.html` CTA
    rewrite (no raw URL).

## Acceptance criteria

- [x] A logged-in Provenancier sees no *Enroll* CTA, and visiting `/community/enroll` redirects to
  submit. *(pytest confirmed — 132 passed)*
- [x] *Review queue* is absent from the nav for anonymous/non-staff visitors and present for staff;
  verifier sign-in is reachable from `/community/login`. *(pytest confirmed)*
- [x] An applicant can select specific members on the enroll page; those identities land in
  `PeerVouchRequest.requested_vouchers` (filtered to real members). *(pytest confirmed)*
- [x] An enrolled member sees pending requests at `/community/vouch-requests`, with the ones that
  asked them flagged, and can vouch in one click (self- and double-vouch still blocked). *(pytest confirmed)*

## Out of scope

- Live nav notification badge / counts (per-page API cost) — the asked-me highlight lives on the
  vouch-requests page. Possible later enhancement.
- Email/push notifications — the seed has no such channel; "notification" here is the in-UI
  flagged list a member sees when they log in.
- Any change to the underlying vouch/threshold mechanics (§03 logic) — presentation + a discovery
  endpoint only.

## Addendum — 2026-09-20, staff-aware nav account CTA

Follow-up found reviewing the operator flow after this TODO's nav changes shipped: the nav's
account CTA keyed only on the Provenancier session, so a logged-in verifier still saw a useless
Provenancier "Log in" and had no nav logout (only the Review-queue page had one). Fixed in
`base.html`: "Log in" is now hidden for `request.user.is_staff`, and the Admin dropdown gained a
"Log out" → `bundledui-verifier-logout` item. Two tests added to `test_bundledui.py`. Full detail
in BLUEPRINT §07's 2026-09-20 Decision Log entry.

## Verification (developer-run — sandbox blocks Bash here)

1. `python manage.py makemigrations communityauth && python manage.py migrate`
2. `pytest tests/test_communityauth.py tests/test_bundledui.py`
3. Manual: enroll members A & B (founding → admin-approve); enroll C selecting A as requested
   voucher; log in as A → *Vouch requests* shows C highlighted "asked you" → Vouch; confirm no
   *Enroll* tab while logged in, no *Review queue* tab as non-staff, verifier sign-in on `/community/login`.
