from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    name = "application"

    def ready(self):
        from .signals import application_state_chaged
        from actstream import registry

        registry.register(self.get_model("Application"))
