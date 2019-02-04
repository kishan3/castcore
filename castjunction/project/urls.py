"""Urls for project and jobs."""
from django.conf.urls import url, include
from .views import JobViewSet, JobLikeViewSet
from users.views import EducationSearchView, ExperienceSearchView, SearchFieldView
from rest_framework.routers import DefaultRouter


from rest_framework_extensions.routers import (
    ExtendedSimpleRouter as SimpleRouter
)
router = SimpleRouter()

(
    router.register(r'jobs', JobViewSet)
    .register(r'likes',
              JobLikeViewSet,
              'jobs-like',
              parents_query_lookups=['receiver_object_id'])
)

router_search = DefaultRouter()
# router_search.register(r'job', JobSearchView, base_name="job-search")
router_search.register(r'education', EducationSearchView, base_name="education-search")
router_search.register(r'experience', ExperienceSearchView, base_name="experience-search")
router_search.register(r'field', SearchFieldView, base_name="field-search")

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^search/', include(router_search.urls), name='search_view'),
]
