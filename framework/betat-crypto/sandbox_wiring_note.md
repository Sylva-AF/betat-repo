# SUPERSEDED — do not wire this in.
#
# This note and the files alongside it (contribute.html, contribute_view.py,
# passphrase_auth.py) assume a codebase shape that doesn't match the real
# framework (wrong ApiClient interface, wrong auth-method identifiers,
# hardcoded threshold instead of CommunityConfig.peer_vouch_threshold, a
# communityauth/peer_vouch.py file that doesn't exist). The real
# implementation of passphrase-assisted enrollment lives in
# communityauth/passphrase.py + bundledui/views.py's enroll_view and
# provenancier_login_view — see BLUEPRINT.md §03 Decision Log, 2026-09.
# Safe for the developer to `git rm -r framework/betat-crypto`.
#
# --- original note kept below for reference only ---

# Sandbox wiring note — passphrase auth + Contribute tab
# Read before touching any file.

## What this delivers

1. `common/passphrase_auth.py` — deterministic keypair derivation from passphrase
2. `bundledui/contribute_view.py` — single Contribute tab replacing Enroll + Submit
3. `bundledui/templates/bundledui/community/contribute.html` — state-aware template

## Authority chain

Per BLUEPRINT authority rule (spec → blueprint → TODOs → code):
Before wiring, add one BLUEPRINT §07 Decision Log entry:

  "Enroll and Submit tabs merged into a single Contribute tab.
   ContributeView detects session enrollment token and renders the
   appropriate form. Auth method fields render conditionally from
   CommunityConfig.auth_methods — peer_vouch shows name only,
   crypto_key shows passphrase fields, institutional shows
   institution ID. Crypto_key uses passphrase-derived Ed25519
   keypairs (scrypt KDF, community_id as salt) — passphrase never
   stored. Raw hex keys suppressed from all UI. Existing enroll
   and submit URLs preserved for API compatibility."

## File placement

  passphrase_auth.py  →  betat_community/common/passphrase_auth.py
  contribute_view.py  →  betat_community/bundledui/contribute_view.py
  contribute.html     →  betat_community/bundledui/templates/
                         bundledui/community/contribute.html

## urls.py changes (bundledui/urls.py)

Read the file first. Add ONE import and ONE URL pattern.
Follow the existing hyphenated convention (no app_name namespace):

  from .contribute_view import ContributeView

  path('contribute/', ContributeView.as_view(), name='bundledui-contribute'),

DO NOT remove the existing enroll/ and submit/ URL patterns.
They must stay for API compatibility — the contribute tab routes
through them via ApiClient internally.

## base.html nav change (bundledui/templates/bundledui/community/base.html)

Read the file first. Replace the two nav links:

  OLD (two links):
    <a href="{% url 'bundledui-enroll' %}" ...>Enroll</a>
    <a href="{% url 'bundledui-submit' %}" ...>Submit</a>

  NEW (one link):
    <a href="{% url 'bundledui-contribute' %}"
       class="{% if 'contribute' in request.resolver_match.url_name %}
              bt-active{% endif %}">
      Contribute
    </a>

Nav result: Records | Contribute | Review queue
(three tabs, not four)

## Active state for Contribute tab

The active class check uses 'contribute' in url_name rather than
exact match — so both the enroll and submit phases of the same URL
keep the tab highlighted. The URL name is 'bundledui-contribute'
so the check is:
  'contribute' in request.resolver_match.url_name

## settings.py — no changes needed

The cryptography package is already in pyproject.toml dependencies.
scrypt is part of cryptography.hazmat — no new pip installs.

## Verification steps

1. python manage.py check — no import errors
2. Browser: visit /community/contribute/
   - With no session token: enroll form renders
   - peer_vouch community: only name field shown, no passphrase
   - crypto_key community: name + passphrase + confirm shown
3. Complete enrollment (peer_vouch): confirm session gets token
4. Browser: visit /community/contribute/ again
   - Submit form renders (has token)
   - peer_vouch: no passphrase field on submit form
   - crypto_key: passphrase field shown on submit form
5. Old URLs still work: /community/enroll/ and /community/submit/
   (they render their own templates — not broken)
6. pytest tests/ — no regressions

## What does NOT change

- communityauth/ models, views, serializers — untouched
- enrollment API endpoint (/betat/enroll/) — untouched
- submission API endpoint (/betat/submit/) — untouched
- existing enroll.html and submit.html templates — untouched
- forms.py, api_client.py, rendering.py — untouched
- betat.css — untouched
- All existing test fixtures — untouched

## Security notes

1. Passphrase sent over HTTPS POST — never logged, never stored
   in session, DB, or any file. The view uses it, derives the key,
   and it vanishes with the request.

2. The scrypt KDF (n=2**14) takes ~100ms server-side — acceptable
   UX, meaningful brute-force resistance. Do not lower n.

3. community_id as salt means the same passphrase produces a
   different keypair on every Betat community. A passphrase
   compromise on one community does not expose others.

4. Ed25519 is the correct algorithm — fast, small (32-byte public
   key, 64-byte signature), modern, supported by the cryptography
   package already present.

5. Forgotten passphrase = re-enrollment with new passphrase and
   new keypair. Old records still exist with the old public key.
   This is the correct behaviour — no recovery path needed or
   appropriate in a zero-knowledge system.

## Future work (not in scope for v0.1 — note in BLUEPRINT)

- Move passphrase derivation to the browser (Web Crypto API)
  so the server never sees the passphrase at all. Higher privacy,
  more complex implementation.
- Multi-method enrollment UI (when communities enable more than
  one auth method and want the Provenancier to choose).
- institutional auth UI (institution_id field is wired in the
  view but the template only shows it — full institutional
  verification flow is not yet designed).
