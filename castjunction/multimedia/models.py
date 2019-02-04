"""Models for storing multimedia data for project."""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from utils.mixins import CommonFieldsMixin
from utils import choices
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class Image(CommonFieldsMixin):
    """Images."""

    image_w = models.PositiveIntegerField(blank=True, null=True, default=0)
    image_h = models.PositiveIntegerField(blank=True, null=True, default=0)
    image = models.ImageField(
        upload_to='images/%Y/%m/%d',
        height_field='image_h',
        width_field='image_w',
        default=None,
        blank=True)
    thumbnail_200x200 = ImageSpecField(
        source='image',
        processors=[ResizeToFill(200, 200)],
        format='JPEG',
        options={'quality': 85})

    thumbnail_150x150 = ImageSpecField(
        source='image',
        processors=[ResizeToFill(150, 150)],
        format='JPEG',
        options={'quality': 85})

    is_private = models.BooleanField(
        default=False,
        help_text='Weather the image is private or public.')
    image_type = models.CharField(max_length=1, choices=choices.MEDIA_TYPE_CHOICES, default=choices.GENERIC)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class Video(CommonFieldsMixin):
    """Videos."""

    video = models.FileField(
        upload_to='videos/%Y/%m/%d')
    is_private = models.BooleanField(
        default=False,
        help_text='Weather the video file is private or public.')
    video_type = models.CharField(max_length=1, choices=choices.MEDIA_TYPE_CHOICES, default=choices.GENERIC)
    video_thumbnail = models.ImageField(
        upload_to='videos/thumbnails/%Y/%m/%d',
        blank=True,
        null=True,)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    link = models.URLField(null=True, blank=True)


class Audio(CommonFieldsMixin):
    """Audios."""

    audio = models.FileField(
        upload_to='audios/%Y/%m/%d')
    is_private = models.BooleanField(
        default=False,
        help_text='Weather the audio file is private or public.')
    audio_type = models.CharField(max_length=1, choices=choices.MEDIA_TYPE_CHOICES, default=choices.GENERIC)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
