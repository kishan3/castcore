"""Main urls file for castjunction."""
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.core.urlresolvers import reverse_lazy
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter
from oscar.app import application as oscar_application
from custom_oscarapi.app import application as api

router = DefaultRouter()

admin.autodiscover()


urlpatterns = [
    url(r'^', include('user_tokens.urls')),
    url(r'^', include('users.urls')),
    url(r'^', include('project.urls')),
    url(r'^', include('application.urls')),
    url(r'^', include('multimedia.urls')),
    url(r'^', include('notifications.urls')),
    url(r'^api/', include(api.urls)),
    url(r'^messages/', include('postman.urls', namespace='postman', app_name='postman')),
    url(r'^review/', include('review.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^referrals/', include('pinax.referrals.urls')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^api/v1/', include(router.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r"^likes/", include("pinax.likes.urls", namespace="pinax_likes")),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/django-ses/', include('django_ses.urls')),
    url(r'^docs/', include('rest_framework_docs.urls')),
    # the 'api-root' from django rest-frameworks default router
    # http://www.django-rest-framework.org/api-guide/routers/#defaultrouter
    url(r'^$', RedirectView.as_view(url=reverse_lazy('api-root'), permanent=False)),
    url(r'', include(oscar_application.urls)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if 'silk' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]
