"""Urls for multimedia CRUD operations."""
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImageUploadViewSet,
    VideoUploadViewSet,
    AudioUploadViewSet,
    JobImageUploadViewSet,
)


router = DefaultRouter()
router.register(r"images", ImageUploadViewSet, "images")
router.register(r"videos", VideoUploadViewSet, "videos")
router.register(r"audios", AudioUploadViewSet, "audios")

router2 = DefaultRouter()
router2.register(r"images", JobImageUploadViewSet, "jobimages")

urlpatterns = [
    url(r"^users/(?P<user_id>[0-9]+)/", include(router.urls)),
    url(r"^jobs/(?P<job_id>[0-9]+)/", include(router2.urls)),
]
