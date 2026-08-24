"""Plain server-rendered forms for enroll/submit/review. One combined
enroll form (rather than per-method forms swapped via JS) — the bundled UI
ships with zero JavaScript, so all method-specific fields are shown at
once, labeled by which method they belong to; the operator only fills in
the ones matching their chosen method.
"""
from django import forms


class EnrollForm(forms.Form):
    method = forms.ChoiceField(label='Authentication method')
    identity = forms.CharField(label='Identity / handle')
    display_name = forms.CharField(label='Display name (optional)', required=False)

    # community_peer_vouching
    vouchers = forms.CharField(
        label='Vouchers (comma-separated identities of existing members)', required=False,
    )
    # cryptographic_signature
    public_key = forms.CharField(label='Public key (hex)', required=False)
    signature = forms.CharField(
        label='Signature (hex) — proof of possession, or institutional endorsement',
        required=False,
    )
    # institutional_endorsement
    institution_id = forms.CharField(label='Institution id', required=False)

    def __init__(self, *args, auth_methods=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['method'].choices = [(m, m) for m in auth_methods]

    def applicant_payload(self):
        data = self.cleaned_data
        payload = {'identity': data['identity'], 'display_name': data['display_name']}
        if data['vouchers']:
            payload['vouchers'] = [v.strip() for v in data['vouchers'].split(',') if v.strip()]
        if data['public_key']:
            payload['public_key'] = data['public_key']
        if data['signature']:
            payload['signature'] = data['signature']
        if data['institution_id']:
            payload['institution_id'] = data['institution_id']
        return payload


class SubmitForm(forms.Form):
    title = forms.CharField(label='Title (optional)', required=False)
    location = forms.CharField(label='Content location (URI/DOI/IPFS)')
    content_hash = forms.CharField(label='Content hash (sha256:...)')
    language = forms.CharField(label='Language code', initial='en')
    declaration_accepted = forms.BooleanField(
        label='I declare this content was originated by a human being, as described above.',
    )


class ReviewActionForm(forms.Form):
    decision = forms.ChoiceField(choices=[('accept', 'Accept'), ('reject', 'Reject')])
    reason = forms.CharField(label='Reason (for reject)', required=False)
