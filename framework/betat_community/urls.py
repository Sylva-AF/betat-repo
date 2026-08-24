"""
URL configuration for betat_community project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from betat_community.bundledui.views import landing_view
from betat_community.communityauth.api.views import EnrollView
from betat_community.federation.api.views import ChangesView, InfoView, RecordDetailView, RecordsView
from betat_community.workflow.api.views import QueueView, ReviewView, SubmitView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('betat/enroll', EnrollView.as_view(), name='betat-enroll'),
    path('betat/submit', SubmitView.as_view(), name='betat-submit'),
    path('betat/queue', QueueView.as_view(), name='betat-queue'),
    path('betat/review/<int:submission_id>', ReviewView.as_view(), name='betat-review'),
    path('betat/info', InfoView.as_view(), name='betat-info'),
    path('betat/records', RecordsView.as_view(), name='betat-records'),
    path('betat/records/<str:record_id>', RecordDetailView.as_view(), name='betat-record-detail'),
    path('betat/changes', ChangesView.as_view(), name='betat-changes'),
    # bundled UI (§07) — human-facing pages, under /community/ so they
    # never collide with /betat/ (the API)
    path('community/', include('betat_community.bundledui.urls')),
    # first-run landing page + readiness checklist (§08) — the one page
    # allowed to claim the root path
    path('', landing_view, name='bundledui-landing'),
]
