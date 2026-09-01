# TODO — Manual eyeball test (enroll → submit → verify)

> Status: in progress — environment works end-to-end (`betat start` serves the
> real community UI); walkthrough itself stopped partway through Enroll.
> Depends on: 01-12 (exercises the whole stack) · Blocks: shipping — TODO 10's
> automated acceptance test proves the API path works, this proves a human can
> actually click through it.

## Context

Automated tests (TODO 10) pass, but nobody had actually run `betat init` →
`migrate` → `betat start` → clicked through Enroll/Submit/Review-queue in a
browser, from a genuinely fresh `git clone` — as a real operator would. The
developer started this pass specifically because "eyeball observation matters
for something with this much importance attached to it." This file picks up
where the session ended.

## Test environment (already set up, reusable)

- Host clone: `~/betat-test/betat-repo` (separate from the main dev clone at
  `~/betat-repo` — keep it that way, don't mix eyeball-testing state into the
  main working copy)
- Container: see `DEVELOPMENT.md` Step 1 — needs `--cap-add DAC_OVERRIDE`
- `.env`: `BETAT_DEBUG=true`, `BETAT_ALLOWED_HOSTS=localhost,127.0.0.1,betat-dev.local`
- `CommunityConfig` already created via non-interactive `betat init` with
  **only `community_peer_vouching` enabled** as the auth method:
  ```
  betat init --id test.betat-dev.local --name "Test Community" \
    --domain "general testing" --content-type text \
    --store-uri "http://localhost:8000/betat" \
    --auth-method community_peer_vouching
  ```
- A superuser exists (created via `python manage.py createsuperuser`) — this
  is your verifier account for the Review-queue step later.
- `betat start` confirmed working, serving the real community UI (not the
  installer screen) at `http://localhost:8000/community/`.

## Where the walkthrough stopped

On the Enroll page. Because `community_peer_vouching` is the only enabled
method and `peer_vouch_threshold` defaults to 2, **the very first enrollment
has no one to vouch for it** — a bootstrap gap. The fix (not yet confirmed
run): seed two bootstrap Provenanciers directly via shell, using the same
`persist_provenancier()` helper the plugin itself calls:

```bash
python manage.py shell -c "
from betat_community.communityauth.enrollment import persist_provenancier
persist_provenancier(identity='seed1@test.local', identity_type='peer_attested', authentication_method='community_peer_vouching', display_name='Seed Voucher 1', verification_material={})
persist_provenancier(identity='seed2@test.local', identity_type='peer_attested', authentication_method='community_peer_vouching', display_name='Seed Voucher 2', verification_material={})
print('seeded 2 vouchers')
"
```

Then on the real Enroll form:
- **Identity / handle**: e.g. `me@test.local`
- **Vouchers**: `seed1@test.local, seed2@test.local`

**Not yet confirmed:** whether this was actually run, and whether enrollment
succeeded. Verify with `Provenancier.objects.count()` (should be 3 after) or
just check whether a submission token was issued.

## Tasks — resume here

- [ ] Confirm enrollment completes and a token is issued
- [ ] Submit a real test contribution (Submit page) — need a real or
      plausible `location` (URI/DOI/IPFS) + `content_hash` (sha256:...);
      any placeholder hash works for eyeballing, it doesn't need to
      resolve to real content
- [ ] Log in as the superuser, use the Review queue to accept the submission
- [ ] Confirm the resulting record: `hi_tag: true`, correct `provenancier`
      block, shows up at `/betat/records` and in the community UI's Records
      list, and renders with the correct integrity-state badge
      (RENDERING.md states)
- [ ] Confirm no update/delete path exists anywhere in the UI for the new
      record (TODO 10 already covers this at the API level; this is just a
      visual/UX confirmation, not new test-writing)
- [ ] Optional: also eyeball the browser setup wizard
      (`/community/install/` → "Begin setup") as an alternative to
      `betat init` — untested in a real browser per
      `todos/todo-setup-wizard.md`'s own "still to do" list

## Bugs found and fixed this session (all should already be on `main`)

1. **`.gitignore`'s bare `commands` line** silently excluded every Django
   management command in every app from ever being tracked, since TODO 01.
   Fixed; commit `9724b6b`.
2. **Dead `federation/management/commands/announce.py`+`export.py` stubs**
   (leftover TODO 01 scaffolding) were shadowing the real TODO 09
   implementations in `core`, because `federation` loads after `core` in
   `INSTALLED_APPS`. Deleted, never committed. Fixed alongside the
   `.gitignore` fix; commit `4a7eb2e`.
3. **`betat_community/bundledui/middleware.py`, `wizard_views.py`, the
   `community/`/`installer/`/`setup/` template reorg, and everything else
   from the TODO 07 cosmetics pass + setup wizard** existed locally but had
   never been committed — `betat start` failed outright
   (`ModuleNotFoundError: No module named 'betat_community.bundledui.middleware'`)
   until this landed. Committed in the bulk "BubdleUI upgrade and more"
   commit (`b61468f`, pushed).
4. **A stray `static/bundledui/betat.css`** (flat path, Aug 25, host-owned)
   duplicated the real `static/bundledui/styles/betat.css` (Aug 28,
   container-owned, actually referenced by `{% static %}` in
   `community/base.html`). Deleted the orphan, not committed.
5. **`DEVELOPMENT.md` itself had several real bugs**, all fixed and verified
   against an actual fresh-clone run: venv must be built inside the
   container (not before `docker run`); `pip install -e` must run from
   `/workspace`, not `/workspace/framework`; the container needs
   `--cap-add DAC_OVERRIDE` or every write fails despite running as root;
   `BETAT_SKIP_DNS_CHECK` doesn't exist in the current code (replaced with
   the non-interactive `--id` flag approach); `.env` vars are
   `BETAT_`-prefixed, not bare; `migrate` must run before `betat init`
   (queries a table that doesn't exist yet otherwise).
6. **UI polish** on Enroll/Submit, found via the actual walkthrough: no
   placeholder text anywhere in `forms.py`, several component font sizes
   sat well below the 16px body base, and both forms rendered directly on
   the warm-gray page background with no card panel (unlike record/queue
   pages, which already use `.bt-card`). Fixed in `forms.py`, `betat.css`,
   `enroll.html`, `submit.html` — **staged/committed but not confirmed
   pushed, verify with `git log`/`git status` first.**
7. **No applicant-facing tool exists to generate a `cryptographic_signature`
   keypair** — the only generator (`communityauth/crypto.py`'s
   `generate_keypair()`/`sign()`) is explicitly commented
   `"""Convenience for tests/docs"""`, and `join-a-community.md` claimed no
   software/technical knowledge is ever needed, which isn't true for this
   method. Logged as an open, undecided item in `BLUEPRINT.md`'s Decision
   Log (§03, dated 2026-08) rather than silently building a fix. Doc
   mitigation shipped: `framework-api.md` now has a runnable keypair-gen
   snippet, `join-a-community.md` caveats the method.
   **Not yet committed — see below.**

## Uncommitted as of session end — verify before resuming

Run `git status` in `~/betat-repo` (the main clone, not `betat-test`) first
thing next session. Expected to still be sitting uncommitted:
- `framework-api.md` (new keypair-gen snippet)
- `join-a-community.md` (caveat on the cryptographic-key method)
- `framework/BLUEPRINT.md` (new §03 Decision Log entry)

And double-check (not confirmed pushed, only confirmed staged) whether item
6 above (`forms.py`, `betat.css`, `enroll.html`, `submit.html`) actually made
it into a pushed commit — the session moved on to other things right after
handing off the `git add`/`commit`/`push` commands, without a follow-up
`git log` to confirm.

## Also noticed, not acted on

- `DEVELOPMENT.md`'s file-reference table points at a `ROADMAP.md` that does
  not exist anywhere in the repo — dangling reference, low priority, but a
  reader will hit a 404/missing-file confusion if they go looking for it.
