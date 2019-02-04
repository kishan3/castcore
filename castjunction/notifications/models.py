"""Models for notification management."""
from django.db import models
from django.contrib.postgres.fields import JSONField
from actstream.models import Action as BaseAction


class Action(BaseAction):
    """Custom action model derived from actstream.models.Action."""

    unread = models.BooleanField(default=True, blank=False)
    data = JSONField(null=True, blank=True)

    def mark_as_read(self):
        """Mark action as read."""
        if self.unread:
            self.unread = False
            self.save()

    def mark_as_unread(self):
        """Mark action as unread."""
        if not self.unread:
            self.unread = True
            self.save()
