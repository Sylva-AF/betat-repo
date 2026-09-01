# SUPERSEDED — do not wire this in.
#
# This note and the files alongside it (enrollment_request_model.py,
# peer_vouch_updated.py) assume a codebase shape that doesn't match the
# real framework (a flat communityauth/peer_vouch.py module that doesn't
# exist — the real file is communityauth/plugins/peer_vouch.py; a
# PK-based vouchers list instead of the identity-string shape
# PeerVouchAuth already persists; a hardcoded VOUCH_THRESHOLD instead of
# CommunityConfig.peer_vouch_threshold). The real implementation is the
# Pending outcome type (communityauth/identity.py), PeerVouchRequest
# model, the rewritten PeerVouchAuth.enroll()/add_vouch(), and the new
# VouchView — see BLUEPRINT.md §03 Decision Log, 2026-09. It also fixes a
# gap this note didn't: vouches must now come from an authenticated
# POST /betat/vouch/{id} by the voucher, not a list the applicant names.
# Safe for the developer to `git rm -r framework/betat-enroll`.
#
# --- original note kept below for reference only ---

# Sandbox wiring note — progressive peer_vouch enrollment
# Read fully before touching any file.
# Authority: add BLUEPRINT §03 Decision Log entry first.

## BLUEPRINT §03 Decision Log entry (add before any code changes)

  "Peer_vouch enrollment is now a two-step process. EnrollmentRequest
   (new model in communityauth) accumulates vouches until the threshold
   is met, then auto-promotes via persist_provenancier(). Three states:
   pending_admin (bootstrap: 0-1 existing Provenanciers, admin approves
   directly), pending_vouches (normal: vouch count tracked, partial
   progress saved), approved (threshold met, token issued). The form
   never throws a threshold error — progress is always saved. The
   contribute view renders a third 'pending' phase showing vouch progress.
   add_vouch() and admin_approve() are new entry points in peer_vouch.py."

## Files and placement

  enrollment_request_model.py  →  Add EnrollmentRequest class to
                                   communityauth/models.py
                                   (alongside existing Provenancier model)

  peer_vouch_updated.py        →  Replace communityauth/peer_vouch.py
                                   (or wherever PeerVouchAuth.enroll() lives —
                                   read the file first to confirm the path)

  contribute_pending_template  →  bundledui/templates/bundledui/community/
                                   contribute_pending.html

## Step 1 — Add EnrollmentRequest to models.py

Read communityauth/models.py first.
Add the EnrollmentRequest class from enrollment_request_model.py.
Do NOT remove or modify the existing Provenancier model.

## Step 2 — Make and run migration

  python manage.py makemigrations communityauth
  python manage.py migrate

Confirm the new table exists:
  python manage.py shell -c "
  from betat_community.communityauth.models import EnrollmentRequest
  print('EnrollmentRequest table ok:', EnrollmentRequest.objects.count())
  "

## Step 3 — Update peer_vouch.py

Read the existing peer_vouch.py first to confirm:
  - Where enroll() is defined
  - Whether VOUCH_THRESHOLD already exists (if so, keep the same value)
  - Whether add_vouch() already exists (if so, reconcile)

Replace enroll() with the version from peer_vouch_updated.py.
Add add_vouch(), admin_approve(), and _promote() as new functions.
Keep VOUCH_THRESHOLD = 2 at module level.

## Step 4 — Update the enrollment API view

The enrollment API view (likely communityauth/api/views.py EnrollView)
currently calls enroll() and expects a Provenancier + token back.
It now receives a status dict. Update the response:

  result = enroll(request.data)

  if result['status'] == 'approved':
      return Response({
          'token': result['token'],
          'status': 'approved',
      }, status=201)
  else:
      # pending_vouches or pending_admin — 202 Accepted
      return Response({
          'status':         result['status'],
          'request_id':     result['request_id'],
          'vouch_count':    result.get('vouch_count', 0),
          'vouches_needed': result.get('vouches_needed', 2),
          'message':        result['message'],
      }, status=202)

## Step 5 — Add vouch endpoint to communityauth/api/views.py

New view for existing Provenanciers to vouch for a pending request:

  class VouchView(APIView):
      permission_classes = [IsAuthenticated]

      def post(self, request, request_id):
          from betat_community.communityauth.models import Provenancier
          from betat_community.communityauth.peer_vouch import add_vouch
          try:
              provenancier = Provenancier.objects.get(user=request.user)
          except Provenancier.DoesNotExist:
              return Response(
                  {'detail': 'Only enrolled Provenanciers can vouch.'},
                  status=403
              )
          try:
              result = add_vouch(request_id, provenancier.pk)
          except ValueError as e:
              return Response({'detail': str(e)}, status=404)

          status_code = 201 if result['status'] == 'approved' else 200
          return Response(result, status=status_code)

Add URL: path('vouch/<int:request_id>/', VouchView.as_view(),
              name='communityauth-vouch')

## Step 6 — Update ContributeView session handling

In bundledui/contribute_view.py, update _handle_enroll() response handling:

  if response.status_code == 201:
      # Approved immediately
      data = response.json()
      request.session[SESSION_TOKEN_KEY] = data['token']
      return redirect(reverse('bundledui-contribute'))

  elif response.status_code == 202:
      # Pending — save request_id and status in session
      data = response.json()
      request.session['enroll_request_id'] = data['request_id']
      request.session['enroll_status']     = data['status']
      request.session['enroll_message']    = data['message']
      request.session['enroll_vouch_count'] = data.get('vouch_count', 0)
      return redirect(reverse('bundledui-contribute'))

Update ContributeView.get() to detect the pending phase:

  if request.session.get(SESSION_TOKEN_KEY):
      ctx['phase'] = 'submit'
  elif request.session.get('enroll_request_id'):
      ctx['phase']             = 'pending'
      ctx['enroll_request_id'] = request.session['enroll_request_id']
      ctx['enroll_status']     = request.session.get('enroll_status')
      ctx['enroll_message']    = request.session.get('enroll_message')
      ctx['vouch_count']       = request.session.get('enroll_vouch_count', 0)
  else:
      ctx['phase'] = 'enroll'

## Step 7 — Update contribute.html

Add the pending phase block alongside enroll/submit:

  {% if phase == 'enroll' %}
    ... existing enroll form ...
  {% elif phase == 'submit' %}
    ... existing submit form ...
  {% elif phase == 'pending' %}
    {% include "bundledui/community/contribute_pending.html" %}
  {% endif %}

## Step 8 — Add vouch page to bundledui

A simple page where a logged-in Provenancier submits a vouch.
URL: /community/vouch/<request_id>/
View: reads request_id, confirms user is a Provenancier,
      POSTs to the vouch API endpoint, shows result.
This is a thin view — the heavy logic is in VouchView above.

## Step 9 — Admin panel registration

Add EnrollmentRequest to communityauth/admin.py so verifiers
can approve pending_admin requests through /admin/:

  from .models import EnrollmentRequest

  @admin.register(EnrollmentRequest)
  class EnrollmentRequestAdmin(admin.ModelAdmin):
      list_display  = ['display_name', 'status', 'vouch_count',
                       'authentication_method', 'created_at']
      list_filter   = ['status', 'authentication_method']
      actions       = ['approve_selected', 'reject_selected']

      def vouch_count(self, obj):
          return obj.vouch_count
      vouch_count.short_description = 'Vouches'

      def approve_selected(self, request, queryset):
          from betat_community.communityauth.peer_vouch import admin_approve
          for req in queryset.filter(status='pending_admin'):
              admin_approve(req.pk, admin_note='Approved via admin panel')
      approve_selected.short_description = 'Approve selected requests'

      def reject_selected(self, request, queryset):
          for req in queryset.filter(status__in=['pending_admin','pending_vouches']):
              req.reject(admin_note='Rejected via admin panel')
      reject_selected.short_description = 'Reject selected requests'

## Verification steps

1. python manage.py check — no errors
2. Fresh community (0 Provenanciers):
   - Submit enrollment → 202 pending_admin
   - contribute.html shows "Awaiting administrator approval"
   - Admin approves in /admin/ → token issued
3. One Provenancier exists:
   - Submit enrollment → 202 pending_admin (still bootstrap)
   - Same admin approval flow
4. Two Provenanciers exist:
   - Submit enrollment → 202 pending_vouches, vouch_count=0
   - Message: "Two community members must vouch for you"
   - First Provenancier vouches via /community/vouch/<id>/
   - contribute.html shows one green dot, one empty dot
   - Message: "One member has vouched — one more needed"
   - Second Provenancier vouches
   - Auto-promoted → 201 → token issued → submit form shown
5. pytest tests/ — no regressions in existing suite
   (EnrollmentRequest is a new model, existing tests unaffected)

## What does NOT change

- persist_provenancier() — untouched, called by _promote()
- Provenancier model — untouched
- CryptoKeyAuth enrollment — untouched
- ProvenanceRecord, store, workflow — untouched
- betat.css — untouched
- federation API endpoints — untouched

## Security notes

1. Vouch endpoint requires IsAuthenticated — only enrolled
   Provenanciers can vouch. Unauthenticated requests → 403.
2. add_vouch() is idempotent — the same Provenancier vouching
   twice only counts once. Prevents vouch stuffing.
3. A Provenancier cannot vouch for themselves — the vouch API
   should check that vouching_provenancier_pk != applicant identity.
   Add this check to add_vouch() if not already present.
4. EnrollmentRequest.status is indexed — admin queries on
   pending requests stay fast as the table grows.
