"""Admin panel for applications."""
from django.contrib import admin

from reversion.admin import VersionAdmin

from .models import Application, MobileAppVersion, AuditionInvite


@admin.register(Application)
class ApplicationAdmin(VersionAdmin, admin.ModelAdmin):
    """Application admin."""

    list_display = (
        "id",
        "user",
        "job",
        "state",
        "created_at",
        "updated_at",
        "get_job_id",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )

    def get_job_id(self, obj):
        return obj.job.id


@admin.register(MobileAppVersion)
class MobileAppVersionAdmin(admin.ModelAdmin):
    """Mobile app versions admin."""

    list_display = (
        "version_code",
        "is_required",
        "message",
        "created_at",
        "updated_at",
        "url",
    )


@admin.register(AuditionInvite)
class AuditionInviteAdmin(admin.ModelAdmin):
    """Mobile app versions admin."""

    list_display = ("title", "description", "location", "date")
