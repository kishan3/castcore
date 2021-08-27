from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        from .signals import create_token_account
        from actstream import registry

        registry.register(self.get_model("User"))
        registry.register(self.get_model("Person"))
        registry.register(self.get_model("Company"))
