from django.contrib import admin
from imagekit.admin import AdminThumbnail

from .models import Image

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('image_thumbnail', 'title', 'image', 'content_type', 'content_object')
    readonly_fields = ('image_thumbnail',)
    image_thumbnail = AdminThumbnail(image_field='thumbnail_150x150')
