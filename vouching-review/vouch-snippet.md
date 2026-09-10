Implement the founding-phase admin vouch for peer_vouch enrollment.

This is a design decision, not a bug fix. Add the BLUEPRINT §03 Decision Log entry first, then implement.

BLUEPRINT §03 Decision Log entry:

Founding-phase admin vouch: peer_vouch enrollment now has two phases.
When enrolled Provenancier count < 2, enrollment requests are routed
to the admin (status=pending_admin) — the community administrator's
approval is sufficient for founding members, since no peers exist yet
to vouch. When enrolled count >= 2, the full peer_vouch threshold
applies (2 member vouches required). The transition is automatic —
the system detects which phase it is in; the operator configures
nothing. This closes the bootstrap catch-22 without requiring a
separate bootstrap auth method or any operator-facing configuration.
The founding flag on PeerVouchRequest gives verifiers context in the
review queue.

The rule:

enrolled_count < 2  →  pending_admin (admin approves directly)
enrolled_count >= 2 →  pending_vouches (2 member vouches required)

Changes needed — read each file before editing:

1. communityauth/peer_vouch.py — update enroll()

Read the current file first. After validating display_name, add the enrolled count check before the vouch threshold logic:

python
from betat_community.communityauth.models import Provenancier

enrolled_count = Provenancier.objects.filter(user__is_active=True).count()

if enrolled_count < 2:
    # Founding phase — route to admin approval
    req = PeerVouchRequest.objects.create(
        display_name=display_name,
        authentication_method='peer_vouch',
        status='pending_admin',
        founding=True,
    )
    return {
        'status':     'pending_admin',
        'request_id': req.pk,
        'message':    (
            'Your enrollment request has been received. '
            'This community is just getting started — the administrator '
            'will review and approve founding member requests directly.'
        ),
    }

# enrolled_count >= 2 — existing peer_vouch threshold logic unchanged

2. communityauth/models.py — add founding field to PeerVouchRequest

Read the current model. Add one boolean field:

python
founding = models.BooleanField(
    default=False,
    help_text='True for the first two members — admin approval sufficient.'
)

Run python manage.py makemigrations communityauth and python manage.py migrate after adding the field.

3. Enrollment API view — handle pending_admin response

Read the current enrollment view. The pending_admin response is already a 202 — confirm it reaches the bundled UI correctly. No change needed if the view already handles the status dict from enroll() and returns 202 for non-approved states.

4. contribute_pending.html — update the pending_admin message

Replace any technical vouch language with:

html
{% if enroll_status == 'pending_admin' %}
<p class="bt-body" style="margin-bottom:1.5rem">
  This community is just getting started — the administrator
  will review and approve founding member requests directly.
  You will be able to submit content once your enrollment is approved.
</p>
<div class="wz-done-list">
  <div class="wz-done-item">
    <div class="milestone-dot" style="background:var(--bt-green)"></div>
    <span>Request submitted</span>
  </div>
  <div class="wz-done-item">
    <div style="width:8px;height:8px;border-radius:50%;
                border:1.5px solid var(--bt-border);flex-shrink:0"></div>
    <span style="color:var(--bt-muted)">Awaiting administrator approval</span>
  </div>
</div>
{% endif %}

No request ID shown. No vouch instructions. No technical language.

5. communityauth/admin.py — update the verifier review queue label

Read the current admin registration for PeerVouchRequest. Update list_display to show the founding flag, and add context to the approval action label:

python
def founding_label(self, obj):
    return '⭐ Founding member' if obj.founding else ''
founding_label.short_description = 'Type'

list_display = ['display_name', 'status', 'founding_label',
                'vouch_count', 'created_at']

The verifier seeing a founding request in the queue understands immediately: this person is one of the first two members, admin approval is all that's needed.

6. Drop the init-time guard

Do not implement any warning in betat init about peer_vouch bootstrap. The founding-phase design makes it unnecessary — the system handles it automatically. If a guard was partially added in a previous session, remove it.

Verification steps:

Fresh community (0 enrolled):
  → Enroll via peer_vouch
  → 202 pending_admin, founding=True
  → contribute.html shows founding-phase message (no vouch language)
  → Admin approves in /admin/ → token issued → submit form shown

One enrolled Provenancier:
  → Second person enrolls via peer_vouch
  → 202 pending_admin, founding=True (still < 2)
  → Admin approves → token issued

Two enrolled Provenanciers:
  → Third person enrolls
  → 202 pending_vouches (full peer_vouch — founding phase over)
  → Vouch progress shown — two member vouches required

What does NOT change:

persist_provenancier() — untouched
add_vouch() — untouched
crypto_key enrollment — untouched
The peer_vouch threshold value (2) — untouched
betat.css — untouched
Existing test suite — the new founding field has a default so existing fixtures are unaffected
