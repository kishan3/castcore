"""
Default application configuration.
In use as of Django 1.7.
"""
from django.apps import AppConfig


class PostmanConfig(AppConfig):
    name = 'postman'

    def ready(self):
        from .models import setup
        from actstream import registry
        registry.register(self.get_model('Message'))
        setup()
