"""bundledui's views — plain, server-rendered, zero JavaScript. The §07
views (enroll/submit/queue/records) read and write exclusively through
ApiClient, never the ORM, per COMMUNITY_FRAMEWORK.md's "bundled UI
consumes the public JSON API only" rule. The one narrow exception there is
Token.objects.get_or_create() for an already-Django-session-authenticated
verifier — that's token bootstrapping for DRF auth, not a business-logic
shortcut; no Submission/ProvenanceRecord/CommunityConfig is ever touched
directly by those views.

landing_view (§08) is a different kind of page — an operator/ops status
view, not part of the Layer 2 consumption model §07's rule targets — and
checks `connection.vendor` directly: the DB engine is infrastructure
state, not provenance data, and has no business being exposed on any
public API. It still reuses ApiClient for the "is this install
configured" check rather than querying CommunityConfig directly, since
that part genuinely is API-shaped.

Session use: a Provenancier's enroll token lives in request.session after
a successful enroll — that session *is* "being logged in" for this seed
UI. There is no separate "log back in as an existing provenancier" flow;
enrolled identities without unusable passwords (all of them, by §03
design) have no browser-login path here. That's a known, honest gap for
the seed implementation, not solved by this section.
"""
import json

import django
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import connection
from django.shortcuts import redirect, render
from rest_framework.authtoken.models import Token

import betat_community
from betat_community.core.models import CommunityConfig

from .api_client import ApiClient
from .forms import EnrollForm, ReviewActionForm, SubmitForm
from .rendering import check_content_hash, content_type_label, language_label, record_is_tampered


def _decorate_record(record):
    record['tampered'] = record_is_tampered(record)
    record['content_type_display'] = content_type_label(record['content']['type'])
    record['language_display'] = language_label(record['content']['language'])
    return record


def enroll_view(request):
    api = ApiClient(server_name=request.get_host())
    status, info = api.get('/betat/info')
    if status != 200:
        return render(request, 'bundledui/community/not_configured.html', status=503)
    auth_methods = info['auth_methods']

    if request.method == 'POST':
        form = EnrollForm(request.POST, auth_methods=auth_methods)
        if form.is_valid():
            status, data = api.post('/betat/enroll', {
                'method': form.cleaned_data['method'],
                'applicant': form.applicant_payload(),
            })
            if status == 201:
                request.session['provenancier_token'] = data['token']
                request.session['provenancier_identity'] = data['identity']
                messages.success(request, f"Enrolled as '{data['identity']}'. You can now submit a contribution.")
                return redirect('bundledui-submit')
            messages.error(request, data.get('error', {}).get('message', 'Enrollment failed.'))
    else:
        form = EnrollForm(auth_methods=auth_methods)

    return render(request, 'bundledui/community/enroll.html', {'form': form, 'community': info})


def submit_view(request):
    token = request.session.get('provenancier_token')
    if not token:
        messages.info(request, 'Enroll first to get a submission token.')
        return redirect('bundledui-enroll')

    if request.method == 'POST':
        form = SubmitForm(request.POST)
        if form.is_valid():
            api = ApiClient(token=token, server_name=request.get_host())
            status, data = api.post('/betat/submit', form.cleaned_data)
            if status == 201:
                messages.success(request, f"Submission #{data['id']} received — pending verifier review.")
                return redirect('bundledui-submit')
            messages.error(request, data.get('error', {}).get('message', 'Submission failed.'))
    else:
        form = SubmitForm()

    return render(request, 'bundledui/community/submit.html', {
        'form': form, 'identity': request.session.get('provenancier_identity'),
    })


def verifier_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                messages.error(request, 'This account is not a verifier.')
            else:
                login(request, user)
                return redirect('bundledui-queue')
    else:
        form = AuthenticationForm(request)
    return render(request, 'bundledui/community/verifier_login.html', {'form': form})


def verifier_logout_view(request):
    logout(request)
    return redirect('bundledui-records')


def _verifier_token(request):
    """Auto-provisions a DRF token for an already-session-authenticated
    staff user — not a business-logic shortcut, see module docstring."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return None
    token, _created = Token.objects.get_or_create(user=request.user)
    return token.key


def queue_view(request):
    token = _verifier_token(request)
    if not token:
        return redirect('bundledui-verifier-login')

    status, pending = ApiClient(token=token, server_name=request.get_host()).get('/betat/queue')
    if status != 200:
        messages.error(request, 'Could not load the review queue.')
        pending = []

    return render(request, 'bundledui/community/queue.html', {
        'submissions': pending, 'form': ReviewActionForm(),
    })


def review_action_view(request, submission_id):
    if request.method != 'POST':
        return redirect('bundledui-queue')
    token = _verifier_token(request)
    if not token:
        return redirect('bundledui-verifier-login')

    form = ReviewActionForm(request.POST)
    if form.is_valid():
        api = ApiClient(token=token, server_name=request.get_host())
        status, data = api.post(f'/betat/review/{submission_id}', form.cleaned_data)
        if status == 200:
            messages.success(request, f'Submission #{submission_id}: {data["status"]}.')
        else:
            messages.error(request, data.get('error', {}).get('message', 'Review failed.'))
    return redirect('bundledui-queue')


def records_list_view(request):
    current_page = int(request.GET.get('page', 1))
    params = {'page': current_page}
    if request.GET.get('hi_only'):
        params['hi_only'] = request.GET['hi_only']

    status, page = ApiClient(server_name=request.get_host()).get('/betat/records', params)
    if status != 200:
        messages.error(request, 'Could not load records.')
        page = {'results': [], 'next': None, 'previous': None, 'count': 0}

    records = [_decorate_record(r) for r in page['results']]
    return render(request, 'bundledui/community/records_list.html', {
        'count': page['count'],
        'records': records,
        # page.next/previous from DRF are absolute API URLs (wrong host
        # and path for this UI) — link by page number against our own
        # URL instead of reusing them verbatim.
        'has_next': page['next'] is not None,
        'has_previous': page['previous'] is not None,
        'next_page': current_page + 1,
        'previous_page': current_page - 1,
    })


def record_detail_view(request, record_id):
    status, record = ApiClient(server_name=request.get_host()).get(f'/betat/records/{record_id}')
    if status != 200:
        return render(request, 'bundledui/community/record_unverified.html', {'record_id': record_id})

    record_json = json.dumps(record, indent=2, sort_keys=True)
    record = _decorate_record(record)
    content_state = None if record['tampered'] else check_content_hash(record['content'])

    return render(request, 'bundledui/community/record_detail.html', {
        'record': record,
        'content_state': content_state,
        'record_json': record_json,
    })


# Real docs, live on the public Jekyll site (betat.org) — §11's Framework
# Reference pages. Not locally hosted: this app runs on a bare VPS with no
# assumption of a docs build step, and the public site already exists,
# free, for exactly this (see BLUEPRINT §11 Decision Log).
DOCS_CLI = 'https://betat.org/framework-cli.html'
DOCS_API = 'https://betat.org/framework-api.html'


def install_view(request):
    """Phase 1 installer screen (TODO 07 amendment). BetatConfiguredMiddleware
    redirects every other community-facing page here until a CommunityConfig
    exists; this view's own redirect-when-configured check is what makes
    /community/install unreachable again once setup completes."""
    if CommunityConfig.objects.exists():
        return redirect('bundledui-landing')
    return render(request, 'bundledui/installer/install.html', {
        'version': getattr(betat_community, '__version__', '0.1.0'),
        'django_version': django.get_version(),
    })


def landing_view(request):
    db_ready = connection.vendor != 'sqlite'
    status, info = ApiClient(server_name=request.get_host()).get('/betat/info')
    configured = status == 200

    checklist = [
        {
            'label': 'Install a robust database engine',
            'done': db_ready,
            'detail': 'PostgreSQL recommended; SQLite is for evaluation only.',
            'docs': DOCS_CLI,
        },
        {
            'label': "Set up your community's provenance assertions and records",
            'done': configured,
            'detail': 'Declare your HI standard at or above the Betat baseline.',
            'docs': DOCS_CLI,
        },
        {
            'label': 'Initiate your chosen authentication method(s)',
            'done': configured and bool(info.get('auth_methods')),
            'detail': 'Select deliberately from the protocol list.',
            'docs': DOCS_CLI,
        },
        {
            'label': 'Adapt your own UI bundle if desired',
            'done': True,
            'detail': 'The bundled UI works as-is; replace or supplement it via the public API.',
            'docs': DOCS_API,
        },
    ]

    return render(request, 'bundledui/community/landing.html', {
        'configured': configured,
        'community': info if configured else None,
        'checklist': checklist,
    })
