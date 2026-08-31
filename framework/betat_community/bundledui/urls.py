"""bundledui's own human-facing paths, kept under /community/ so they
never collide with the /betat/ API surface (BLUEPRINT §0) and don't claim
`/` — that's §08's first-run landing page, out of this section's scope.
"""
from django.urls import path

from . import views
from .wizard_views import (
    SetupDone,
    SetupStep1Welcome,
    SetupStep2Identity,
    SetupStep3Content,
    SetupStep4Store,
    SetupStep5Auth,
    SetupStep6Declaration,
    SetupStep7Confirm,
)

urlpatterns = [
    path('install', views.install_view, name='bundledui-install'),
    path('setup', SetupStep1Welcome.as_view(), name='bundledui-setup-1'),
    path('setup/identity', SetupStep2Identity.as_view(), name='bundledui-setup-2'),
    path('setup/content', SetupStep3Content.as_view(), name='bundledui-setup-3'),
    path('setup/store', SetupStep4Store.as_view(), name='bundledui-setup-4'),
    path('setup/auth', SetupStep5Auth.as_view(), name='bundledui-setup-5'),
    path('setup/declaration', SetupStep6Declaration.as_view(), name='bundledui-setup-6'),
    path('setup/confirm', SetupStep7Confirm.as_view(), name='bundledui-setup-7'),
    path('setup/done', SetupDone.as_view(), name='bundledui-setup-done'),
    path('enroll', views.enroll_view, name='bundledui-enroll'),
    path('submit', views.submit_view, name='bundledui-submit'),
    path('queue', views.queue_view, name='bundledui-queue'),
    path('queue/login', views.verifier_login_view, name='bundledui-verifier-login'),
    path('queue/logout', views.verifier_logout_view, name='bundledui-verifier-logout'),
    path('queue/review/<int:submission_id>', views.review_action_view, name='bundledui-review-action'),
    path('records', views.records_list_view, name='bundledui-records'),
    path('records/<str:record_id>', views.record_detail_view, name='bundledui-record-detail'),
]
