"""apps.py for multimedia app."""
from django.apps import AppConfig


class MultimediaConfig(AppConfig):
    name = "multimedia"

    def ready(self):
        from .signals import update_multimedia
