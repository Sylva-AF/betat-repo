from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command

from betat_community.core.models import BASELINE_HI_STANDARD, CommunityConfig

pytestmark = pytest.mark.django_db


def _init(**overrides):
    kwargs = dict(
        id="example.org",
        name="Example Community",
        domain="marine biology",
        content_type="scientific_observation",
        store_uri="https://example.org/records",
        auth_methods=["community_peer_vouching"],
    )
    kwargs.update(overrides)
    # init's operator-declaration and email steps are deliberately
    # unbypassable (see BLUEPRINT/TODO 01 — anti-automation is the point
    # for a real install), so tests simulate the human answers a real
    # operator would give rather than skipping the prompts.
    with patch("builtins.input", side_effect=["yes", "test-operator@example.org"]):
        call_command("init", **kwargs)


def test_init_writes_valid_config():
    _init()
    config = CommunityConfig.objects.get(id="example.org")
    assert config.hi_standard == BASELINE_HI_STANDARD
    assert config.auth_methods == ["community_peer_vouching"]


def test_malformed_fqdn_rejected():
    with pytest.raises(CommandError):
        _init(id="Not A Domain")


def test_second_init_rejected_single_config_per_install():
    _init()
    with pytest.raises(CommandError):
        _init(id="second.example.org")


def test_hi_standard_addition_strengthens_baseline():
    _init(hi_standard_addition="human-authored, AI-untouched")
    config = CommunityConfig.objects.get(id="example.org")
    assert config.hi_standard.startswith(BASELINE_HI_STANDARD)
    assert "human-authored, AI-untouched" in config.hi_standard


def test_model_rejects_hi_standard_that_drops_baseline():
    config = CommunityConfig(
        id="example.org",
        name="Example Community",
        domain="marine biology",
        content_type="scientific_observation",
        hi_standard="a made-up weaker standard",
        auth_methods=["community_peer_vouching"],
        store_uri="https://example.org/records",
    )
    with pytest.raises(ValidationError):
        config.full_clean()


def test_model_rejects_empty_auth_methods():
    config = CommunityConfig(
        id="example.org",
        name="Example Community",
        domain="marine biology",
        content_type="scientific_observation",
        auth_methods=[],
        store_uri="https://example.org/records",
    )
    with pytest.raises(ValidationError):
        config.full_clean()
