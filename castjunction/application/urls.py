"""Urls for project and jobs."""
from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from .views import (
    ApplicationViewSet,
    MobileAppVersionView,
    CheckUserProfileInfo,
    MultipleApplicationsViewSet,
    MultipleUsersViewSet,
)

router = DefaultRouter()
router.register(r"applications", ApplicationViewSet, base_name="user_applications")

urlpatterns = [
    url(r"^jobs/(?P<job_id>[0-9]+)/", include(router.urls)),
    url(
        r"^jobs/(?P<job_id>[0-9]+)/check",
        CheckUserProfileInfo.as_view(),
        name="check_user_profile",
    ),
    url(
        r"multiple-applications/",
        MultipleApplicationsViewSet.as_view(),
        name="multiple_applications",
    ),
    url(
        r"jobs/(?P<job_id>[0-9]+)/multiple-users/",
        MultipleUsersViewSet.as_view(),
        name="multiple_users_applications",
    ),
    url(
        r"^mobile-app-version/(?P<version_code>[0-9]+)/",
        MobileAppVersionView.as_view(),
        name="mobile_app_version",
    ),
]
