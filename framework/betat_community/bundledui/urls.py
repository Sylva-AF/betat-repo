"""bundledui's own human-facing paths, kept under /community/ so they
never collide with the /betat/ API surface (BLUEPRINT §0) and don't claim
`/` — that's §08's first-run landing page, out of this section's scope.
"""
from django.urls import path

from . import views

urlpatterns = [
    path('enroll', views.enroll_view, name='bundledui-enroll'),
    path('submit', views.submit_view, name='bundledui-submit'),
    path('queue', views.queue_view, name='bundledui-queue'),
    path('queue/login', views.verifier_login_view, name='bundledui-verifier-login'),
    path('queue/logout', views.verifier_logout_view, name='bundledui-verifier-logout'),
    path('queue/review/<int:submission_id>', views.review_action_view, name='bundledui-review-action'),
    path('records', views.records_list_view, name='bundledui-records'),
    path('records/<str:record_id>', views.record_detail_view, name='bundledui-record-detail'),
]
