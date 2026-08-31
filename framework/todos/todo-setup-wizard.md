# TODO — Setup wizard wiring (§07 follow-on)

> Status: done — wired, tested; not yet run (developer action, see handoff)
> Depends on: 07-bundled-ui.md (cosmetics pass done, installer wired)
> Blocks: nothing — wizard is an alternative path to betat init, not a dependency

## Context

The setup wizard is the browser alternative to `betat init`. Its goal
is identical: write a valid `CommunityConfig` and a `.env` accountability
record, leaving the instance ready for members to use.

The validation logic is already written in `bundledui/wizard_views.py`
and mirrors `core/management/commands/init.py` exactly — same DNS check,
same field validation, same `CommunityConfig.full_clean()` before save,
same `_write_env()` call. The templates exist in `bundledui/templates/
bundledui/setup/` as navigation shells. The sandbox session's job is
to wire the views to URLs and confirm template paths — not to write
new validation logic.

## Read before starting

1. `core/management/commands/init.py` — the CLI source of truth.
   Every validation in the wizard must produce the same outcome.
   When in doubt, match init.py, not the wizard's own assumptions.
2. `bundledui/wizard_views.py` — the views to wire. Read it fully
   before touching urls.py. All eight step views are defined here.
3. `bundledui/urls.py` — where the URL patterns go. Follow the existing
   hyphenated convention: `bundledui-setup-1`, not `bundledui:setup-1`.
4. `bundledui/templates/bundledui/setup/` — confirm all nine template
   files are present: `base_setup.html`, `step1_welcome.html` through
   `step7_confirm.html`, `step8_done.html`.

## Tasks

### 1. Import the wizard views into urls.py

In `bundledui/urls.py`, add the import:

```python
from .wizard_views import (
    SetupStep1Welcome, SetupStep2Identity, SetupStep3Content,
    SetupStep4Store,   SetupStep5Auth,     SetupStep6Declaration,
    SetupStep7Confirm, SetupDone,
)
```

### 2. Register the eight URL patterns

Add to `urlpatterns` in `bundledui/urls.py`, following the existing
hyphenated convention (no `app_name` namespace):

```python
path('setup/',             SetupStep1Welcome.as_view(),    name='bundledui-setup-1'),
path('setup/identity/',    SetupStep2Identity.as_view(),   name='bundledui-setup-2'),
path('setup/content/',     SetupStep3Content.as_view(),    name='bundledui-setup-3'),
path('setup/store/',       SetupStep4Store.as_view(),      name='bundledui-setup-4'),
path('setup/auth/',        SetupStep5Auth.as_view(),       name='bundledui-setup-5'),
path('setup/declaration/', SetupStep6Declaration.as_view(),name='bundledui-setup-6'),
path('setup/confirm/',     SetupStep7Confirm.as_view(),    name='bundledui-setup-7'),
path('setup/done/',        SetupDone.as_view(),            name='bundledui-setup-done'),
```

### 3. Confirm template render paths in each view

Each view calls `render(request, 'bundledui/setup/stepN_*.html', ctx)`.
Confirm the paths match what actually exists in the `setup/` directory.
If any path is wrong, update the `render()` call in the view — do not
move the template files. The correct paths are:

```
bundledui/setup/step1_welcome.html
bundledui/setup/step2_identity.html
bundledui/setup/step3_content.html
bundledui/setup/step4_store.html
bundledui/setup/step5_auth.html
bundledui/setup/step6_declaration.html
bundledui/setup/step7_confirm.html
bundledui/setup/step8_done.html
```

And the wizard base template (extended by all step templates):
```
bundledui/setup/base_setup.html
```

### 4. Confirm the installer's "Begin setup" link resolves

In `bundledui/templates/bundledui/installer/install.html`, the
"Begin setup" `<a>` tag must point to `bundledui-setup-1`:

```html
<a href="{% url 'bundledui-setup-1' %}" class="install-cta">
  Begin setup
</a>
```

If it currently has a `#` placeholder, update it now. This is the
connection that makes the installer and the wizard one coherent flow.

### 5. Verify parity with betat init

Read `core/management/commands/init.py` and confirm each wizard step
maps to its CLI equivalent:

| Wizard step | init.py equivalent         | Field(s)                        |
|-------------|----------------------------|---------------------------------|
| Step 2      | community_id prompt        | id — FQDN, DNS-checked          |
| Step 2      | name prompt                | name                            |
| Step 2      | domain prompt              | domain (knowledge domain)       |
| Step 3      | content_type prompt        | content_type (CONTENT_TYPE_CHOICES) |
| Step 3      | hi_standard_addition prompt | hi_standard (optional addition) |
| Step 4      | store_uri prompt           | store_uri                       |
| Step 5      | auth_methods prompt        | auth_methods (list)             |
| Step 6      | declaration acceptance     | OPERATOR_DECLARATION text       |
| Step 6      | operator_email prompt      | written to .env                 |
| Step 7      | final save                 | CommunityConfig + _write_env()  |

The `OPERATOR_DECLARATION` string in `wizard_views.py` must match
the one in `init.py` exactly — same wording, same accountability
record. If they differ, update `wizard_views.py` to match `init.py`.

### 6. Check AUTH_METHODS list matches the protocol floor

In `wizard_views.py`, `AUTH_METHODS` is:
```python
AUTH_METHODS = ['peer_vouch', 'crypto_key', 'institutional']
```

Confirm this matches the valid methods in `communityauth/` (the seed
plugins: `PeerVouchAuth`, `CryptoKeyAuth`, `InstitutionalAuth`).
If `communityauth` exposes a list of valid method names, import and
use that rather than maintaining a duplicate list here.

### 7. Run manage.py check

```bash
python manage.py check
```

Confirms URL conf is valid, no import errors, no missing template
directories. Fix any errors before running the browser test.

### 8. Browser walkthrough — all eight steps

Walk through the complete wizard in a browser:

- `/community/setup/` → Step 1 welcome renders, "Begin →" navigates
- `/community/setup/identity/` → form submits, DNS check runs on
  community_id, invalid domain shows error and stays on step 2,
  valid domain advances to step 3
- Steps 3-6 → each form validates, errors shown inline, back
  navigation returns to previous step with fields pre-filled
  from session
- Step 7 → review table shows all collected values correctly,
  "Confirm and go live" POST writes CommunityConfig
- Step 8 → success screen shows community name and id, three
  next-step commands, link to community landing
- After step 8: visit `/community/setup/` → redirects to community
  landing (not the wizard — already configured)
- After step 8: visit `/community/install/` → redirects to community
  landing (installer gone)

### 9. Confirm .env accountability record written

After step 7 commits:

```bash
cat .env
```

Should contain:
```
BETAT_OPERATOR_EMAIL=<email entered in step 6>
BETAT_DECLARATION_ACCEPTED=true
BETAT_DECLARED_COMMUNITY_ID=<community_id from step 2>
```

These are the accountability fields. `BETAT_DB` is separate and only
present if the operator configured PostgreSQL via `betat init` — the
wizard does not handle database setup (that is `betat init`'s scope
and the CLI path).

## What does NOT change

- `wizard_views.py` validation logic — already mirrors init.py
- Template HTML structure — navigation shells are complete
- `betat.css` — wizard uses inline CSS in `base_setup.html`
- `views.py`, `forms.py`, `api_client.py` — untouched

## Acceptance criteria

- [ ] `python manage.py check` passes with all eight wizard URLs registered
- [ ] Complete wizard walkthrough succeeds in browser without errors
- [ ] Invalid community_id (non-resolving domain) shows error on step 2
      and does not advance
- [ ] Back navigation on any step returns with form pre-filled from session
- [ ] Step 7 confirm table shows all values correctly before commit
- [ ] `CommunityConfig.objects.count()` == 1 after completion
- [ ] `.env` contains the three accountability fields
- [ ] After completion, `/community/install/` and `/community/setup/`
      both redirect to the community landing — wizard and installer
      are permanently gone
- [ ] `pytest tests/` — no regressions in the existing test suite

## Security note

The wizard uses `request.session` to carry state between steps.
Django's session framework signs session data — an attacker cannot
tamper with session values without the secret key. `SESSION_KEY =
'betat_setup'` is cleared on completion (`_clear_setup(request)`
in `SetupDone`). Verify the session is cleared after step 8 so a
browser refresh of the done page does not re-attempt the commit.

## Session handoff (2026-08-29)

### The TODO's premise didn't hold — flagging for future reference

This file said `bundledui/wizard_views.py` "is already written" and the
job was just to wire URLs. It didn't exist in the repo at all when this
session started (same pattern as `framework/betat-installer/` and
`framework/ROADMAP.md` earlier in this project — a TODO citing files that
were never actually committed). The user then supplied the actual file via
`framework/betat-wizard/`. Worth double-checking a TODO's "already exists"
claims against the actual filesystem before trusting them, going forward.

### What was wrong in the supplied file, and what Claude fixed

- **`AUTH_METHODS = ['peer_vouch', 'crypto_key', 'institutional']` — none
  of these are real.** The actual protocol-list keys (`communityauth/
  floor.py`'s `PROTOCOL_LIST`, keyed by each plugin's `method_name`) are
  `community_peer_vouching`, `cryptographic_signature`,
  `institutional_endorsement`. Fixed by deriving `AUTH_METHODS =
  list(PROTOCOL_LIST)` instead of a hand-maintained list — this was
  already this TODO's own task 6 suggestion ("if communityauth exposes a
  list of valid method names, import and use that").
- **DNS check, email validation, `OPERATOR_DECLARATION`, and the `.env`
  writer were hand-copied from `init.py` instead of imported.** Copies
  drift; imports can't. Now imported directly from
  `betat_community.core.management.commands.init`. `OPERATOR_DECLARATION`
  happened to already match verbatim, so no behavior changed there — this
  just makes future drift impossible instead of merely unlikely.
- **`SetupStep7Confirm.post()` used a bare `except Exception`** around
  `config.full_clean(); config.save()`, which would silently swallow real
  bugs (e.g. an `AttributeError`) as if they were validation failures, and
  had no guard against a second tab/process completing setup first (every
  other step's `get()` checks `_already_configured()`; this one's `post()`
  didn't). Fixed: narrowed to `except ValidationError`, added the same
  early-return guard `get()` already had, and dropped the redundant
  `config.full_clean()` call — `CommunityConfig.save()` already calls
  `full_clean()` internally (`core/models.py`), so the explicit call was
  validating twice for nothing. Also found the model's own `clean()`
  already refuses a second `CommunityConfig` regardless (BLUEPRINT §2
  single-config assumption) — the explicit guard is for a cleaner
  redirect-to-landing UX, not the only thing preventing a duplicate.
- **`SetupStep7Confirm.get()` never read `setup_error` back from the
  session**, even though `step7_confirm.html` renders an `{% if error %}`
  banner and `post()` sets that key on failure — every other step's
  `get()` does this pop, step 7's didn't. Without it, a failed final
  submission silently bounced the user back to the review page with zero
  explanation. Fixed by adding the same `ctx['error'] =
  request.session.pop('setup_error', None)` line.
- **`step_title` gap from the earlier `base_setup.html` fix**: that
  session's fix for the duplicate-`{% block step_title %}` bug (see
  `todos/07-bundled-ui.md`) turned the progress-bar's step label into a
  plain `{{ step_title }}` variable, but no view supplied it. Added a
  `STEP_TITLES` dict and included it in `_base_context()`.
- Removed an unused `from django.utils.text import slugify` import.

### Files written/changed this session

- `bundledui/wizard_views.py` — written fresh with the fixes above (the
  version in `framework/betat-wizard/` was the starting point, not copied
  verbatim)
- `bundledui/urls.py` — added the wizard import and 8 URL patterns,
  **without** trailing slashes (`'setup'`, `'setup/identity'`, ... —
  matches this app's existing convention for every other route; the
  TODO's own suggested patterns used trailing slashes, not followed)
- `bundledui/templates/bundledui/installer/install.html` — "Begin setup"
  now points at `{% url 'bundledui-setup-1' %}` instead of the `#`
  placeholder
- `bundledui/middleware.py` — updated the `/community/setup` exemption's
  comment (was "Phase 3, not built yet"; wizard is now built)
- `tests/test_setup_wizard.py` — new, covers the acceptance criteria list
  below plus the specific bugs found above (the race-condition guard, the
  clean-error-on-model-validation-failure path, session pre-fill on back
  navigation)

### Update — developer ran it: 115/116 passed, `manage.py check` clean

`python manage.py check` passed with no issues. `pytest tests/` (116
tests, the full suite including the new `test_setup_wizard.py`) had one
failure: `test_setup_step2_rejects_non_resolving_domain` — the domain
`this-should-not-exist.invalid` actually resolved on the developer's
machine. RFC 2606 reserves `.invalid` to guarantee non-resolution, but
real-world resolvers (corporate DNS, NXDOMAIN-hijacking ISPs, sandboxed
container resolvers that answer everything) frequently don't honor it in
practice. The positive-resolution tests (`example.org`, `localhost`) are
fine to leave as real DNS lookups — well-known domains resolving is a safe
bet almost everywhere, and this matches `test_core.py`'s own existing
precedent. But a test asserting something does *not* resolve can't safely
depend on real network behavior at all. Fixed by mocking
`wizard_views._check_domain_dns` directly for that one test instead of
relying on a magic non-resolving hostname. Not yet re-run — every other
test in the file already passed on the developer's real environment.

### Still to do (developer actions)

1. ~~`python manage.py check`~~ — done, clean.
2. Re-run `pytest tests/` to confirm the DNS-mock fix above actually
   fixes the one failure (115/116 passed before the fix).
3. Full browser walkthrough per this file's task 8 — not done.
4. Once verified, delete `framework/betat-wizard/` (mirrored into the
   real app now) — Claude has no file-delete capability.
