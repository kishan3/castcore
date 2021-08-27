"""Notification urls."""
from django.conf.urls import include, url
from push_notifications.api.rest_framework import (
    APNSDeviceViewSet,
)
from rest_framework.routers import DefaultRouter

from .views import GCMDeviceViewSet

router = DefaultRouter()
router.register(r"device/apns", APNSDeviceViewSet)
router.register(r"device/gcm", GCMDeviceViewSet)

urlpatterns = [
    url(r"^", include(router.urls)),
    url("^activity/", include("actstream.urls")),
]
