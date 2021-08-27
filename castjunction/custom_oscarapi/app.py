from oscarapi.app import RESTApiApplication
from .urls import urlpatterns


class MyRESTApiApplication(RESTApiApplication):
    def get_urls(self):
        urls = super(MyRESTApiApplication, self).get_urls()
        return urlpatterns + urls


application = MyRESTApiApplication()
