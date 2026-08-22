"""CommunityConfig — the identity every record this install issues inherits.

Field-level source of truth: COMMUNITY_FRAMEWORK.md "Community Identity" /
"CommunityConfig"; see BLUEPRINT.md §2.
"""
import re

from django.core.exceptions import ValidationError
from django.db import models

BASELINE_HI_STANDARD = "human-originated, community-verified"

# PROVENANCE_SPEC.md "Content Types" table — fixed enum, spec-permanent.
CONTENT_TYPE_CHOICES = [
    ("text", "Text"),
    ("scientific_observation", "Scientific observation"),
    ("creative_work", "Creative work"),
    ("oral_knowledge", "Oral knowledge"),
    ("personal_testimony", "Personal testimony"),
    ("indigenous_knowledge", "Indigenous knowledge"),
    ("religious_text", "Religious text"),
    ("legal_record", "Legal record"),
    ("historical_record", "Historical record"),
    ("other", "Other"),
]

# Lowercase labels, alphanumeric + hyphen, no empty labels, at least one dot.
_FQDN_LABEL = r"[a-z0-9]([a-z0-9-]*[a-z0-9])?"
_FQDN_RE = re.compile(rf"^{_FQDN_LABEL}(\.{_FQDN_LABEL})+$")


def validate_fqdn(value):
    if value != value.lower():
        raise ValidationError("Community id must be lowercase.", code="invalid_fqdn")
    if not _FQDN_RE.match(value):
        raise ValidationError(
            "Community id must be a syntactically valid FQDN with "
            "non-empty labels (e.g. 'example.org').",
            code="invalid_fqdn",
        )


def validate_auth_methods(value):
    if not isinstance(value, list) or not value:
        raise ValidationError(
            "At least one authentication method is required.",
            code="empty_auth_methods",
        )
    if not all(isinstance(v, str) and v.strip() for v in value):
        raise ValidationError(
            "Authentication methods must be non-empty strings.",
            code="invalid_auth_methods",
        )
    # Membership against the protocol list is the "floor rule enforced in
    # config load" — owned by communityauth (§03, BLUEPRINT §3), not here.


class CommunityConfig(models.Model):
    """A community's declared identity. Single-config-per-install (seed
    assumption, BLUEPRINT §2) — enforced in clean()."""

    id = models.CharField(primary_key=True, max_length=253, validators=[validate_fqdn])
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=200)
    content_type = models.CharField(max_length=32, choices=CONTENT_TYPE_CHOICES)
    hi_standard = models.TextField(default=BASELINE_HI_STANDARD)
    auth_methods = models.JSONField(validators=[validate_auth_methods])
    store_uri = models.CharField(max_length=500)

    def clean(self):
        super().clean()
        if not self.hi_standard.startswith(BASELINE_HI_STANDARD):
            raise ValidationError(
                {
                    "hi_standard": ValidationError(
                        "hi_standard must include the Betat baseline "
                        f'("{BASELINE_HI_STANDARD}") — communities may '
                        "strengthen it, never replace or weaken it.",
                        code="weakens_baseline",
                    )
                }
            )
        if CommunityConfig.objects.exclude(pk=self.pk).exists():
            raise ValidationError(
                "Only one CommunityConfig is supported per install (seed "
                "assumption, BLUEPRINT §2).",
                code="multiple_configs",
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.id
