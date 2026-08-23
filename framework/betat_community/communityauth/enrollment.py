"""Shared persistence step for a successful enroll(): create the Django
User + DRF Token + Provenancier row together. Used by every plugin so
enroll() implementations only handle plugin-specific validation."""
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.authtoken.models import Token

from .models import Provenancier

User = get_user_model()


def persist_provenancier(identity, identity_type, authentication_method, display_name, verification_material):
    with transaction.atomic():
        user = User.objects.create_user(username=f'provenancier:{uuid.uuid4()}', password=None)
        user.set_unusable_password()
        user.save(update_fields=['password'])
        provenancier = Provenancier.objects.create(
            user=user,
            identity=identity,
            identity_type=identity_type,
            authentication_method=authentication_method,
            display_name=display_name,
            verification_material=verification_material,
        )
        token = Token.objects.create(user=user)
    return provenancier, token
