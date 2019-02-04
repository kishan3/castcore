"""Admin panel for Jobs and Groups."""
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from pinax.referrals.models import ReferralResponse
from reversion.admin import VersionAdmin
from imagekit.admin import AdminThumbnail

from multimedia.models import Image

from .models import Job, Group, Key


class MyModelAdmin(admin.ModelAdmin):

    def delete_model(self, request, obj):
        obj.active = False
        obj.save()

    def get_queryset(self, request):
        qs = super(MyModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(referral__user=request.user)


class ImageInline(GenericTabularInline):
    model = Image
    fields = ("active", "admin_image", "title", "image", "image_w", "image_h", "image_type",)
    readonly_fields = ("admin_image",)
    admin_image = AdminThumbnail(image_field="thumbnail_150x150")


@admin.register(Job)
class JobAdmin(VersionAdmin):
    list_display = ('id', 'title', 'role_position', 'status', 'submission_deadline',
                    'created_at', 'created_by', 'required_gender')
    list_filter = ("status", "created_at", "submission_deadline",
                   "role_position")
    search_fields = ("title", "role_position", "created_by")
    inlines = [
        ImageInline,
    ]

    # define the raw_id_fields
    raw_id_fields = ('location',)
    # define the autocomplete_lookup_fields
    autocomplete_lookup_fields = {
        'fk': ['location'],
    }


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'start_date',)


@admin.register(Key)
class KeyAdmin(admin.ModelAdmin):
    list_display = ('key_name', 'key_type', 'title_director_display')


admin.site.unregister(ReferralResponse)


@admin.register(ReferralResponse)
class ReferralResponseAdmin(MyModelAdmin):
    list_display = (
        "user",
        "referral",
        # "session_key",
        # "ip_address",
        "action"
    )
    readonly_fields = ("referral", "session_key", "user", "ip_address", "action")
    list_filter = ("action", "created_at")
    search_fields = ("referral__code", "referral__user__username", "ip_address")
