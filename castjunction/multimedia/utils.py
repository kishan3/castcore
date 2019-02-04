"""uiti methods for multimedia."""
import magic
from rest_framework.exceptions import ValidationError

CONTENT_TYPES = ['image', 'video', 'audio']
MAX_UPLOAD_SIZE = 52428800


def verify_image(image):
    """Verify upload image."""
    if not image:
        raise ValidationError("Image is required to upload.")

    # assert isinstance(image, InMemoryUploadedFile), "Image rewrite has been only tested on in-memory upload backend"

    # Make sure the image is not too big, so that PIL trashes the server
    if image:
        if image._size > 4*1024*1024:
            raise ValidationError("Image file too large - the limit is 4 megabytes")

    # Then do header peak what the image claims
    image.file.seek(0)
    mime = magic.from_buffer(image.file.getvalue(), mime=True)
    mime = mime.decode("utf-8")
    if mime not in ("image/png", "image/jpeg"):
        raise ValidationError("Image is not valid. Please upload a JPEG or PNG image.")


def verify_video(video):
    """Verify upload video."""
    content_type = video.content_type.split('/')[0]
    if content_type in CONTENT_TYPES:
        if video._size > MAX_UPLOAD_SIZE:
            raise ValidationError("Please keep filesize under {0}. Current filesize {1}".format(MAX_UPLOAD_SIZE, video._size))
    else:
        raise ValidationError("File type is not supported")


def verify_audio(audio):
    """Verify upload audio."""
    content_type = audio.content_type.split('/')[0]
    if content_type in CONTENT_TYPES:
        if audio._size > MAX_UPLOAD_SIZE:
            raise ValidationError("Please keep filesize under {0}. Current filesize {1}".format(MAX_UPLOAD_SIZE, audio._size))
    else:
        raise ValidationError("File type is not supported")
