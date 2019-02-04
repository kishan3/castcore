"""Signal for multimedia app."""
from django.db.models.signals import pre_save
from django.dispatch import receiver

from users.utils import increase_percentage
from utils import choices
from .models import Image


@receiver(pre_save, sender=Image)
def update_multimedia(sender, instance, *args, **kwargs):
    """Update users profile % if cetain conditions are met."""
    if instance.content_type.name == 'person':
        user = instance.content_object
        if user.images.filter(image_type=choices.PRIMARY).count() == 0 and instance.image_type == choices.PRIMARY:
            increase_percentage(user, 'images')

        if user.images.filter(image_type=choices.COVER).count() == 0 and instance.image_type == choices.COVER:
            increase_percentage(user, 'images')


@receiver(pre_save)
def update_extra_multimedia(sender, instance, *args, **kwargs):
    """Update if there is profile or cover image and user uploads audio, video or image."""
    list_of_models = ('Image', 'Video', 'Audio')
    if sender.__name__ in list_of_models:
        user = instance.content_object
        generic_image_count = user.images.filter(image_type=choices.GENERIC).count()
        videos_count = getattr(user, 'videos').count()
        audios_count = getattr(user, 'audios').count()
        if sender.__name__ == 'Image':
            if generic_image_count == 0 and instance.image_type == choices.GENERIC:
                increase_percentage(user, 'extra_multimedia')
        if sender.__name__ in ['Video', 'Audio']:
            if generic_image_count == 0 and videos_count == 0 and audios_count == 0:
                increase_percentage(user, 'extra_multimedia')
