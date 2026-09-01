"""Plain server-rendered forms for enroll/submit/review. One combined
enroll form (rather than per-method forms swapped via JS) — the bundled UI
ships with zero JavaScript, so all method-specific fields are shown at
once, labeled by which method they belong to; the operator only fills in
the ones matching their chosen method.
"""
from django import forms


class EnrollForm(forms.Form):
    method = forms.ChoiceField(label='Authentication method')
    identity = forms.CharField(
        label='Identity / handle',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. name@example.com or a unique handle'}),
    )
    display_name = forms.CharField(
        label='Display name (optional)', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Jane, or leave blank to stay pseudonymous'}),
    )

    # community_peer_vouching
    vouchers = forms.CharField(
        label='Vouchers (comma-separated identities of existing members)', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'alice@example.com, bob@example.com'}),
    )
    # cryptographic_signature — either paste a public_key + signature
    # directly (technical path, unchanged), or choose a passphrase and let
    # the server derive + self-sign the keypair (BLUEPRINT §03 Decision
    # Log, 2026-09 — for applicants who can't manage a keyfile).
    public_key = forms.CharField(
        label='Public key (hex)', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'hex-encoded public key'}),
    )
    signature = forms.CharField(
        label='Signature (hex) — proof of possession, or institutional endorsement',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'hex-encoded signature'}),
    )
    passphrase = forms.CharField(
        label='Passphrase (alternative to pasting a public key/signature)',
        required=False, widget=forms.PasswordInput(render_value=False),
    )
    passphrase_confirm = forms.CharField(
        label='Confirm passphrase', required=False, widget=forms.PasswordInput(render_value=False),
    )
    # institutional_endorsement
    institution_id = forms.CharField(
        label='Institution id', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. your-institution.org'}),
    )

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
    title = forms.CharField(
        label='Title (optional)', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Field notes from the March 2026 survey'}),
    )
    location = forms.CharField(
        label='Content location (URI/DOI/IPFS)',
        widget=forms.TextInput(attrs={'placeholder': 'https://example.com/... or ipfs://... or doi:...'}),
    )
    content_hash = forms.CharField(
        label='Content hash (sha256:...)',
        widget=forms.TextInput(attrs={'placeholder': 'sha256:...'}),
    )
    language = forms.CharField(label='Language code', initial='en')
    declaration_accepted = forms.BooleanField(
        label='I declare this content was originated by a human being, as described above.',
    )


class ReviewActionForm(forms.Form):
    decision = forms.ChoiceField(choices=[('accept', 'Accept'), ('reject', 'Reject')])
    reason = forms.CharField(label='Reason (for reject)', required=False)
