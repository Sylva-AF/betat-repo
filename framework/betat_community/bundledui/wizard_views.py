"""bundledui/wizard_views.py

Setup wizard — browser alternative to `betat init`. Eight steps, Django
session carries state between POSTs. Final POST writes CommunityConfig +
.env accountability record.

Validation is not reimplemented here: DNS checking, email validation, the
operator declaration text, and the .env accountability write are imported
directly from core/management/commands/init.py rather than hand-copied, so
the wizard and the CLI can never silently drift apart on wording or
outcome. AUTH_METHODS is likewise derived from communityauth.floor's own
protocol list rather than a maintained duplicate.

Conventions, matching bundledui/views.py:
- No ORM shortcuts except CommunityConfig (this IS the config setup)
- Session key: 'betat_setup' holds a dict of collected values
- URL names: hyphenated, no app_name namespace (e.g. bundledui-setup-1)
- Redirects to bundledui-landing on completion or if already configured
"""
import django

import betat_community
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from betat_community.communityauth.floor import PROTOCOL_LIST
from betat_community.core.management.commands.init import (
    OPERATOR_DECLARATION,
    _check_domain_dns,
    _validate_email,
    _write_env_record,
)
from betat_community.core.models import (
    BASELINE_HI_STANDARD,
    CONTENT_TYPE_CHOICES,
    CommunityConfig,
)

SESSION_KEY = 'betat_setup'
TOTAL_STEPS = 7  # steps 1-7 are form/info steps; step 8 is done
AUTH_METHODS = list(PROTOCOL_LIST)  # protocol-listed methods, single source of truth

STEP_TITLES = {
    1: 'Welcome',
    2: 'Community identity',
    3: 'Content type',
    4: 'Records location',
    5: 'Authentication',
    6: 'Declaration',
    7: 'Confirm',
}


# ── Helpers ────────────────────────────────────────────────────────────────

def _already_configured():
    return CommunityConfig.objects.exists()


def _get_setup(request):
    return request.session.get(SESSION_KEY, {})


def _save_setup(request, data):
    setup = _get_setup(request)
    setup.update(data)
    request.session[SESSION_KEY] = setup
    request.session.modified = True


def _clear_setup(request):
    request.session.pop(SESSION_KEY, None)


def _format_validation_error(exc):
    """Mirrors init.py Command._format_validation_error — same shape of
    message whether the config was rejected via the CLI or the wizard."""
    if hasattr(exc, 'message_dict'):
        parts = [f"{field}: {'; '.join(msgs)}" for field, msgs in exc.message_dict.items()]
        return ' | '.join(parts)
    return '; '.join(exc.messages)


def _base_context(request, step):
    return {
        'step': step,
        'total_steps': TOTAL_STEPS,
        'step_title': STEP_TITLES.get(step, ''),
        'setup': _get_setup(request),
        'version': getattr(betat_community, '__version__', '0.1.0'),
        'django_version': django.get_version(),
    }


# ── Step views ─────────────────────────────────────────────────────────────

class SetupStep1Welcome(View):
    """Step 1 — welcome and orientation. No form."""

    def get(self, request):
        if _already_configured():
            return redirect(reverse('bundledui-landing'))
        return render(request, 'bundledui/setup/step1_welcome.html',
                      _base_context(request, 1))

    def post(self, request):
        return redirect(reverse('bundledui-setup-2'))


class SetupStep2Identity(View):
    """Step 2 — community_id (DNS-checked), name, knowledge domain."""

    def get(self, request):
        if _already_configured():
            return redirect(reverse('bundledui-landing'))
        ctx = _base_context(request, 2)
        ctx['error'] = request.session.pop('setup_error', None)
        return render(request, 'bundledui/setup/step2_identity.html', ctx)

    def post(self, request):
        community_id = request.POST.get('community_id', '').strip().lower()
        name = request.POST.get('name', '').strip()
        domain = request.POST.get('domain', '').strip()

        if not community_id or not name or not domain:
            request.session['setup_error'] = 'All fields are required.'
            return redirect(reverse('bundledui-setup-2'))

        ok, err = _check_domain_dns(community_id)
        if not ok:
            request.session['setup_error'] = err
            return redirect(reverse('bundledui-setup-2'))

        _save_setup(request, {
            'community_id': community_id,
            'name': name,
            'domain': domain,
        })
        return redirect(reverse('bundledui-setup-3'))


class SetupStep3Content(View):
    """Step 3 — content_type and optional HI standard addition."""

    def get(self, request):
        if _already_configured():
            return redirect(reverse('bundledui-landing'))
        ctx = _base_context(request, 3)
        ctx['content_type_choices'] = CONTENT_TYPE_CHOICES
        ctx['error'] = request.session.pop('setup_error', None)
        return render(request, 'bundledui/setup/step3_content.html', ctx)

    def post(self, request):
        content_type = request.POST.get('content_type', '').strip()
        addition = request.POST.get('hi_standard_addition', '').strip()

        valid_types = [k for k, _ in CONTENT_TYPE_CHOICES]
        if content_type not in valid_types:
            request.session['setup_error'] = 'Please select a content type.'
            return redirect(reverse('bundledui-setup-3'))

        hi_standard = BASELINE_HI_STANDARD
        if addition:
            hi_standard = f'{BASELINE_HI_STANDARD}; {addition}'

        _save_setup(request, {
            'content_type': content_type,
            'hi_standard_addition': addition,
            'hi_standard': hi_standard,
        })
        return redirect(reverse('bundledui-setup-4'))


class SetupStep4Store(View):
    """Step 4 — store_uri (where records are published)."""

    def get(self, request):
        if _already_configured():
            return redirect(reverse('bundledui-landing'))
        ctx = _base_context(request, 4)
        ctx['error'] = request.session.pop('setup_error', None)
        return render(request, 'bundledui/setup/step4_store.html', ctx)

    def post(self, request):
        store_uri = request.POST.get('store_uri', '').strip()
        if not store_uri:
            request.session['setup_error'] = 'Store URI is required.'
            return redirect(reverse('bundledui-setup-4'))

        _save_setup(request, {'store_uri': store_uri})
        return redirect(reverse('bundledui-setup-5'))


class SetupStep5Auth(View):
    """Step 5 — authentication methods (one or more from the protocol list)."""

    def get(self, request):
        if _already_configured():
            return redirect(reverse('bundledui-landing'))
        ctx = _base_context(request, 5)
        ctx['auth_methods'] = AUTH_METHODS
        ctx['error'] = request.session.pop('setup_error', None)
        return render(request, 'bundledui/setup/step5_auth.html', ctx)

    def post(self, request):
        selected = request.POST.getlist('auth_methods')
        selected = [m for m in selected if m in AUTH_METHODS]

        if not selected:
            request.session['setup_error'] = (
                'Select at least one authentication method.'
            )
            return redirect(reverse('bundledui-setup-5'))

        _save_setup(request, {'auth_methods': selected})
        return redirect(reverse('bundledui-setup-6'))


class SetupStep6Declaration(View):
    """Step 6 — operator declaration and contact email."""

    def get(self, request):
        if _already_configured():
            return redirect(reverse('bundledui-landing'))
        ctx = _base_context(request, 6)
        ctx['declaration'] = OPERATOR_DECLARATION
        ctx['error'] = request.session.pop('setup_error', None)
        return render(request, 'bundledui/setup/step6_declaration.html', ctx)

    def post(self, request):
        accepted = request.POST.get('declaration_accepted') == 'yes'
        email = request.POST.get('operator_email', '').strip()

        if not accepted:
            request.session['setup_error'] = (
                'You must accept the declaration to continue.'
            )
            return redirect(reverse('bundledui-setup-6'))

        if not _validate_email(email):
            request.session['setup_error'] = (
                'Please enter a valid contact email address.'
            )
            return redirect(reverse('bundledui-setup-6'))

        _save_setup(request, {
            'declaration_accepted': True,
            'operator_email': email,
        })
        return redirect(reverse('bundledui-setup-7'))


class SetupStep7Confirm(View):
    """Step 7 — review everything, then commit on POST."""

    REQUIRED_FIELDS = (
        'community_id', 'name', 'domain', 'content_type',
        'store_uri', 'auth_methods', 'declaration_accepted',
        'operator_email',
    )

    def get(self, request):
        if _already_configured():
            return redirect(reverse('bundledui-landing'))
        setup = _get_setup(request)

        missing = [k for k in self.REQUIRED_FIELDS if not setup.get(k)]
        if missing:
            return redirect(reverse('bundledui-setup-1'))

        ctx = _base_context(request, 7)
        ctx['auth_methods_display'] = ', '.join(setup.get('auth_methods', []))
        ctx['error'] = request.session.pop('setup_error', None)
        return render(request, 'bundledui/setup/step7_confirm.html', ctx)

    def post(self, request):
        # Guards against a second tab/process completing setup between
        # this tab's GET and POST — same "single config per install"
        # assumption init.py enforces at the top of its own handle().
        if _already_configured():
            return redirect(reverse('bundledui-landing'))

        setup = _get_setup(request)
        if any(not setup.get(k) for k in self.REQUIRED_FIELDS):
            return redirect(reverse('bundledui-setup-1'))

        config = CommunityConfig(
            id=setup['community_id'],
            name=setup['name'],
            domain=setup['domain'],
            content_type=setup['content_type'],
            hi_standard=setup.get('hi_standard', BASELINE_HI_STANDARD),
            auth_methods=setup['auth_methods'],
            store_uri=setup['store_uri'],
        )
        try:
            config.save()  # CommunityConfig.save() runs full_clean() itself
        except ValidationError as exc:
            request.session['setup_error'] = _format_validation_error(exc)
            return redirect(reverse('bundledui-setup-7'))

        # .env write failure is non-fatal — CommunityConfig is the source
        # of truth, same as init.py's own accountability record.
        try:
            _write_env_record(setup['community_id'], setup['operator_email'])
        except OSError:
            pass

        _clear_setup(request)
        return redirect(reverse('bundledui-setup-done'))


class SetupDone(View):
    """Step 8 — success screen with next-step commands."""

    def get(self, request):
        try:
            config = CommunityConfig.objects.get()
        except CommunityConfig.DoesNotExist:
            return redirect(reverse('bundledui-setup-1'))
        return render(request, 'bundledui/setup/step8_done.html', {'config': config})
