"""Serializers for multimedia."""
from rest_framework import serializers
from .models import Image, Video, Audio
from utils import choices
from utils.utils import ChoicesField


class ImageObjectRelatedField(serializers.RelatedField):
    """A custom field to use for the `image` generic relationship."""

    def to_representation(self, value):
        """Get called whenever this serializer field is used to serializer images."""
        # queryset = value.images.all()
        serializer = ImageSerializer(value.image)
        return serializer.data


class ImageSerializer(serializers.ModelSerializer):
    """Image serializer."""

    image_type = ChoicesField(choices=choices.MEDIA_TYPE_CHOICES)
    thumbnail = serializers.FileField(source='thumbnail_150x150', read_only=True)
    thumbnail_200x200 = serializers.FileField(read_only=True)

    class Meta:
        """Meta."""

        model = Image
        fields = ('id', 'title', 'image', 'thumbnail', 'thumbnail_200x200', 'is_private', 'image_type')


class VideoSerializer(serializers.ModelSerializer):
    """Video serializer."""

    video_type = ChoicesField(choices=choices.MEDIA_TYPE_CHOICES)
    thumbnail = serializers.FileField(source='video_thumbnail', read_only=True)

    class Meta:
        """Meta."""

        model = Video
        fields = ('id', 'title', 'video', 'video_type', 'thumbnail', 'is_private',)


class AudioSerializer(serializers.ModelSerializer):
    audio_type = ChoicesField(choices=choices.MEDIA_TYPE_CHOICES)

    class Meta:
        model = Audio
        fields = ('id', 'title', 'audio', 'audio_type', 'is_private',)
