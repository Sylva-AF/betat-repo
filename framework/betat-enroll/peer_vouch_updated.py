"""communityauth/peer_vouch.py — updated enrollment logic.

The key change: enroll() no longer calls persist_provenancier() directly.
Instead it creates or updates an EnrollmentRequest and returns a status dict.
The API view reads the status and responds with 201 (approved) or 202 (pending).

VOUCH_THRESHOLD is the module-level constant so EnrollmentRequest.vouches_needed
can import it without circular imports.
"""
from betat_community.communityauth.enrollment import persist_provenancier
from betat_community.communityauth.models import Provenancier

VOUCH_THRESHOLD = 2   # minimum vouches for peer_vouch enrollment


def _existing_provenancier_count():
    return Provenancier.objects.filter(user__is_active=True).count()


def enroll(data: dict) -> dict:
    """
    Handle a peer_vouch enrollment request.

    Returns a status dict:
      {'status': 'approved', 'provenancier': <obj>, 'token': <token>}
      {'status': 'pending_vouches', 'request_id': <id>, 'vouch_count': N,
       'vouches_needed': M, 'message': <str>}
      {'status': 'pending_admin', 'request_id': <id>, 'message': <str>}

    Never raises for vouching state — progress is always saved.
    Only raises ValidationError for genuinely invalid input
    (missing display_name, duplicate request, etc).
    """
    from django.core.exceptions import ValidationError
    from betat_community.communityauth.enrollment_request_model import EnrollmentRequest

    display_name = (data.get('display_name') or '').strip()
    if not display_name:
        raise ValidationError('display_name is required.')

    existing_count = _existing_provenancier_count()

    # ── Bootstrap: 0 or 1 Provenanciers exist ─────────────────────────────
    # Cannot reach vouch threshold yet — admin approves directly.
    if existing_count < VOUCH_THRESHOLD:
        req = EnrollmentRequest.objects.create(
            display_name          = display_name,
            authentication_method = 'peer_vouch',
            status                = EnrollmentRequest.STATUS_PENDING_ADMIN,
        )
        if existing_count == 0:
            msg = (
                'This is a new community with no members yet. '
                'Your enrollment is awaiting administrator approval. '
                'The administrator will review your request and approve it directly.'
            )
        else:
            msg = (
                f'This community has {existing_count} member — '
                f'peer vouching requires at least {VOUCH_THRESHOLD}. '
                'Your enrollment is awaiting administrator approval.'
            )
        return {
            'status':     EnrollmentRequest.STATUS_PENDING_ADMIN,
            'request_id': req.pk,
            'message':    msg,
        }

    # ── Normal peer_vouch: enough Provenanciers exist ─────────────────────
    # Create or retrieve existing pending request for this display_name.
    # (Resubmitting the same name retrieves the existing request — idempotent)
    req, created = EnrollmentRequest.objects.get_or_create(
        display_name          = display_name,
        authentication_method = 'peer_vouch',
        status__in            = [
            EnrollmentRequest.STATUS_PENDING_VOUCHES,
            EnrollmentRequest.STATUS_PENDING_ADMIN,
        ],
        defaults = {'status': EnrollmentRequest.STATUS_PENDING_VOUCHES}
    )

    vouch_count   = req.vouch_count
    vouches_needed = req.vouches_needed

    if vouch_count == 0:
        msg = (
            'Your enrollment request has been received. '
            'Two community members must vouch for you before '
            'your enrollment is complete. Ask current members to '
            f'vouch for your request (ID: {req.pk}).'
        )
    elif vouch_count < VOUCH_THRESHOLD:
        msg = (
            f'One community member has vouched for you — '
            f'one more vouch needed. '
            f'Ask another member to vouch for request ID: {req.pk}.'
        )
    else:
        # Threshold already met — promote immediately
        # (handles the case where vouch was added via the vouch endpoint
        # and enroll is called again to collect the token)
        return _promote(req)

    return {
        'status':        EnrollmentRequest.STATUS_PENDING_VOUCHES,
        'request_id':    req.pk,
        'vouch_count':   vouch_count,
        'vouches_needed': vouches_needed,
        'message':       msg,
    }


def add_vouch(request_id: int, vouching_provenancier_pk: int) -> dict:
    """
    An existing Provenancier vouches for a pending enrollment request.
    Called by the vouch API endpoint.

    Returns the same status dict as enroll() — so the caller always
    knows the current state after the vouch is recorded.
    """
    from betat_community.communityauth.enrollment_request_model import EnrollmentRequest

    try:
        req = EnrollmentRequest.objects.get(
            pk     = request_id,
            status = EnrollmentRequest.STATUS_PENDING_VOUCHES,
        )
    except EnrollmentRequest.DoesNotExist:
        raise ValueError(f'No pending enrollment request with id {request_id}.')

    threshold_met = req.add_vouch(vouching_provenancier_pk)

    if threshold_met:
        return _promote(req)

    return {
        'status':        EnrollmentRequest.STATUS_PENDING_VOUCHES,
        'request_id':    req.pk,
        'vouch_count':   req.vouch_count,
        'vouches_needed': req.vouches_needed,
        'message':       (
            f'Vouch recorded. '
            f'{req.vouch_count} of {VOUCH_THRESHOLD} vouches received. '
            + (
                'One more vouch needed.'
                if req.vouches_needed == 1
                else f'{req.vouches_needed} more vouches needed.'
            )
        ),
    }


def admin_approve(request_id: int, admin_note: str = '') -> dict:
    """
    A verifier (staff user) directly approves a pending_admin request.
    Called from the admin panel or a future verifier review API.
    """
    from betat_community.communityauth.enrollment_request_model import EnrollmentRequest
    req = EnrollmentRequest.objects.get(
        pk     = request_id,
        status = EnrollmentRequest.STATUS_PENDING_ADMIN,
    )
    return _promote(req, admin_note=admin_note)


def _promote(req, admin_note: str = '') -> dict:
    """
    Promote an EnrollmentRequest to a full Provenancier.
    Calls persist_provenancier() — unchanged from the original flow.
    """
    provenancier, token = persist_provenancier(
        identity              = f'peer_vouch:{req.display_name}',
        identity_type         = 'peer_attested',
        authentication_method = 'peer_vouch',
        display_name          = req.display_name,
        verification_material = {'vouchers': req.vouchers},
    )
    req.approve(admin_note=admin_note)
    return {
        'status':        'approved',
        'provenancier':  provenancier,
        'token':         token.key,
    }
