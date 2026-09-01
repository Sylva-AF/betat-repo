"""bundledui/contribute_view.py

ContributeView — single entry point replacing separate Enroll and Submit tabs.
State-aware: detects session enrollment token and routes to the right step.

Wiring:
  URL name: bundledui-contribute
  Template: bundledui/community/contribute.html (state-aware, renders
            either enroll or submit form based on session state)

Auth method routing (reads from CommunityConfig):
  peer_vouch   → enroll form shows display name + request button only
  crypto_key   → enroll form shows display name + passphrase fields
                 submit form shows passphrase field for signing
  institutional → enroll form shows display name + institution ID

The passphrase never leaves the request — it is used server-side to
derive the keypair, then discarded. It is never stored in the session,
the database, or any log.
"""
import json

from django.shortcuts import render, redirect
from django.urls      import reverse
from django.views     import View

from betat_community.core.models     import CommunityConfig
from betat_community.common.passphrase_auth import (
    public_key_hex, sign_message, verify_signature
)


SESSION_TOKEN_KEY = 'enroll_token'   # existing bundledui session key


def _get_config():
    """Return CommunityConfig or None."""
    try:
        return CommunityConfig.objects.get()
    except CommunityConfig.DoesNotExist:
        return None


def _primary_auth_method(config):
    """Return the first auth method from CommunityConfig."""
    methods = config.auth_methods or []
    return methods[0] if methods else 'peer_vouch'


class ContributeView(View):
    """
    Single Contribute tab — replaces separate Enroll and Submit tabs.
    GET:  render enroll form (no token) or submit form (has token)
    POST: handle whichever form was shown
    """

    def get(self, request):
        config = _get_config()
        if not config:
            return render(request, 'bundledui/community/not_configured.html')

        ctx = self._base_context(request, config)

        if request.session.get(SESSION_TOKEN_KEY):
            ctx['phase'] = 'submit'
        else:
            ctx['phase'] = 'enroll'

        ctx['error'] = request.session.pop('contribute_error', None)
        return render(request, 'bundledui/community/contribute.html', ctx)

    def post(self, request):
        config = _get_config()
        if not config:
            return redirect(reverse('bundledui-landing'))

        phase = request.POST.get('phase', 'enroll')

        if phase == 'enroll':
            return self._handle_enroll(request, config)
        else:
            return self._handle_submit(request, config)

    # ── Enroll ──────────────────────────────────────────────────────────────

    def _handle_enroll(self, request, config):
        auth_method   = _primary_auth_method(config)
        display_name  = request.POST.get('display_name', '').strip()

        if not display_name:
            request.session['contribute_error'] = 'Display name is required.'
            return redirect(reverse('bundledui-contribute'))

        # Build enrollment payload based on auth method
        enroll_data = {
            'display_name':         display_name,
            'authentication_method': auth_method,
        }

        if auth_method == 'peer_vouch':
            # No extra fields — community verifier handles vouching offline
            enroll_data['vouchers'] = []

        elif auth_method == 'crypto_key':
            passphrase = request.POST.get('passphrase', '').strip()
            confirm    = request.POST.get('passphrase_confirm', '').strip()

            if not passphrase:
                request.session['contribute_error'] = 'Passphrase is required.'
                return redirect(reverse('bundledui-contribute'))
            if passphrase != confirm:
                request.session['contribute_error'] = 'Passphrases do not match.'
                return redirect(reverse('bundledui-contribute'))
            if len(passphrase) < 8:
                request.session['contribute_error'] = (
                    'Passphrase must be at least 8 characters.'
                )
                return redirect(reverse('bundledui-contribute'))

            # Derive public key from passphrase — private key never stored
            enroll_data['public_key'] = public_key_hex(passphrase, config.id)
            # Store a flag that this Provenancier uses crypto_key
            # The passphrase itself is NOT stored in the session
            request.session['contrib_auth'] = 'crypto_key'

        elif auth_method == 'institutional':
            institution_id = request.POST.get('institution_id', '').strip()
            if not institution_id:
                request.session['contribute_error'] = 'Institution ID is required.'
                return redirect(reverse('bundledui-contribute'))
            enroll_data['institution_id'] = institution_id

        # POST to the enrollment API (same pattern as existing bundledui views)
        from betat_community.bundledui.api_client import ApiClient
        client   = ApiClient(server_name=request.get_host())
        response = client.post('/betat/enroll/', enroll_data)

        if response.status_code == 201:
            data  = response.json()
            token = data.get('token') or data.get('enrollment_token')
            if token:
                request.session[SESSION_TOKEN_KEY] = token
            return redirect(reverse('bundledui-contribute'))
        else:
            try:
                err = response.json()
                msg = err.get('detail') or str(err)
            except Exception:
                msg = f'Enrollment failed (status {response.status_code}).'
            request.session['contribute_error'] = msg
            return redirect(reverse('bundledui-contribute'))

    # ── Submit ───────────────────────────────────────────────────────────────

    def _handle_submit(self, request, config):
        token        = request.session.get(SESSION_TOKEN_KEY, '')
        location     = request.POST.get('location', '').strip()
        content_hash = request.POST.get('content_hash', '').strip()
        title        = request.POST.get('title', '').strip()
        language     = request.POST.get('language', 'en').strip()
        declaration  = request.POST.get('declaration_accepted') == 'on'
        auth_method  = _primary_auth_method(config)

        if not location or not content_hash:
            request.session['contribute_error'] = (
                'Content location and hash are required.'
            )
            return redirect(reverse('bundledui-contribute'))

        if not declaration:
            request.session['contribute_error'] = (
                'You must accept the declaration to submit.'
            )
            return redirect(reverse('bundledui-contribute'))

        submit_data = {
            'token':        token,
            'location':     location,
            'content_hash': content_hash,
            'title':        title,
            'language':     language,
        }

        if auth_method == 'crypto_key':
            passphrase = request.POST.get('passphrase', '').strip()
            if not passphrase:
                request.session['contribute_error'] = (
                    'Enter your passphrase to sign this submission.'
                )
                return redirect(reverse('bundledui-contribute'))

            # Sign the canonical submission message
            # Message: content_hash + location (what the Provenancier asserts)
            message = f'{content_hash}:{location}'.encode('utf-8')
            submit_data['signature'] = sign_message(passphrase, config.id, message)

        from betat_community.bundledui.api_client import ApiClient
        client   = ApiClient(server_name=request.get_host())
        response = client.post('/betat/submit/', submit_data)

        if response.status_code in (200, 201):
            return redirect(reverse('bundledui-records'))
        else:
            try:
                err = response.json()
                msg = err.get('detail') or str(err)
            except Exception:
                msg = f'Submission failed (status {response.status_code}).'
            request.session['contribute_error'] = msg
            return redirect(reverse('bundledui-contribute'))

    # ── Context ──────────────────────────────────────────────────────────────

    def _base_context(self, request, config):
        return {
            'config':      config,
            'auth_method': _primary_auth_method(config),
            'has_token':   bool(request.session.get(SESSION_TOKEN_KEY)),
        }
