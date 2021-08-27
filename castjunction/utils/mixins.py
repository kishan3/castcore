"""Common fields for all models."""
from django.db import models


class TimeFieldsMixin(models.Model):
    """Time fields to track when object is created."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta."""

        abstract = True


class StatusFieldMixin(models.Model):
    """Status field to make soft delete."""

    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        """Meta."""

        abstract = True


class CommonFieldsMixin(TimeFieldsMixin, StatusFieldMixin):
    """Mixin containing common fields to be added in all models."""

    title = models.CharField(max_length=500, db_index=True, verbose_name="Title")
    description = models.TextField(null=True, blank=True, verbose_name="Description")

    def __str__(self):
        """String representation."""
        return self.title

    class Meta:
        """Meta."""

        abstract = True
