from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'

    def ready(self):
        from .actions import my_action_handler
        from actstream.signals import action
        action.connect(my_action_handler, dispatch_uid='notifications.models.Action')
