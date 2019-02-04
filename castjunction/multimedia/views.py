"""View for multimedia operations."""
import os
import subprocess

from django.core.files.images import ImageFile
from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.permissions import IsAuthenticated

from users.models import User
from project.models import Job

from .models import Image, Video, Audio
from .serializers import ImageSerializer, VideoSerializer, AudioSerializer
from .utils import verify_image, verify_audio, verify_video
from .permissions import IsMultimediaOwner

from utils import choices
from utils.utils import VIDEO_THUMBNAIL_GENERATOR


class JobUploadViewSet(object):
    """Base for upload viewsets."""

    def _get_job(self, id):

        try:
            job = Job.objects.get(pk=id)
            return job
        except Job.DoesNotExist:
            raise NotFound("Job not found.")


class JobImageUploadViewSet(
        JobUploadViewSet,
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """CRUD operations on Image."""

    permission_classes = (IsAuthenticated, )
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def create(self, request, *args, **kwargs):
        """Create Image object when job uploads."""
        job = self._get_job(kwargs.get("job_id"))
        image = request.FILES.get('image')
        if not image:
            raise ValidationError("Image is required to upload.")
        request.data.update({'title': image.name})
        verify_image(image)
        if not request.data.get('image_type'):
            request.data['image_type'] = 'Generic'
        if job.images.count() == 0:
            request.data['image_type'] = 'Primary'
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.validated_data.update({
            'content_object': job,
        })
        try:
            image = Image.objects.create(**serializer.validated_data)
        except Exception as e:
            raise e

        serialied_image = self.get_serializer(image)
        return Response(serialied_image.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """List all images uploaded by job."""
        job = self._get_job(kwargs.get("job_id"))
        queryset = job.images.all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UploadViewSet(object):
    """Base for upload viewsets."""

    def _get_user(self, id):

        try:
            user = User.objects.get(pk=id)
            if user.user_type == User.PERSON:
                user = user.person
            else:
                user = user.company
            return user
        except User.DoesNotExist:
            raise NotFound("User not found.")


class ImageUploadViewSet(
        UploadViewSet,
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    """CRUD operations on Image."""

    permission_classes = (IsAuthenticated, )
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            return (IsMultimediaOwner(),)
        return (IsAuthenticated(),)

    def create(self, request, *args, **kwargs):
        """Create Image object when user uploads."""
        user = self._get_user(kwargs.get("user_id"))
        image = request.FILES.get('image')
        if not image:
            raise ValidationError("Image is required to upload.")
        request.data.update({'title': image.name})
        verify_image(image)
        if not request.data.get('image_type'):
            request.data['image_type'] = 'Generic'
        if user.images.count() == 0:
            request.data['image_type'] = 'Primary'
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.validated_data.update({
            'content_object': user,
        })
        try:
            image = Image.objects.create(**serializer.validated_data)
        except Exception as e:
            raise e

        serialied_image = self.get_serializer(image)
        return Response(serialied_image.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """List all images uploaded by user."""
        user = self._get_user(kwargs.get("user_id"))
        queryset = user.images.all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class VideoUploadViewSet(UploadViewSet, viewsets.ModelViewSet):
    """CRUD operations on Video."""

    permission_classes = (IsAuthenticated, )
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            return (IsMultimediaOwner(),)
        return (IsAuthenticated(),)

    def create(self, request, *args, **kwargs):
        """Create Video object when user uploads."""
        user = self._get_user(kwargs.get("user_id"))
        video = request.FILES.get('video')
        if not video:
            raise ValidationError("Video is required to upload.")
        request.data.update({'title': video.name})
        verify_video(video)
        if not request.data.get('video_type'):
            request.data['video_type'] = choices.GENERIC
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.update({
            'content_object': user,
        })

        try:
            video = Video.objects.create(**serializer.validated_data)
            video_path = "{0}/{1}".format(settings.MEDIA_ROOT, video.video)
            thumbnail_path = os.path.join(settings.MEDIA_ROOT, "videos")
            ffmpeg = VIDEO_THUMBNAIL_GENERATOR.format(video_path, thumbnail_path)
            try:
                subprocess.call(ffmpeg, shell=True)
            except Exception as e:
                raise e
            temp_file = open("{0}/thumb01.jpg".format(thumbnail_path), 'rb')
            video.video_thumbnail.save("thumb_for_{0}.jpg".format(video.title.split('.')[0]), ImageFile(temp_file))
            os.remove("{0}/thumb01.jpg".format(thumbnail_path))
        except Exception as e:
            raise e

        serialied_video = self.get_serializer(video)
        return Response(serialied_video.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """List all videos uploaded by user."""
        user = self._get_user(kwargs.get("user_id"))
        queryset = user.videos.all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AudioUploadViewSet(UploadViewSet, viewsets.ModelViewSet):
    """CRUD on audios by user."""

    serializer_class = AudioSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Audio.objects.all()

    def get_permissions(self):
        if self.request.method == "DELETE":
            return (IsMultimediaOwner(),)
        return (IsAuthenticated(),)

    def create(self, request, *args, **kwargs):
        """Upload videos."""
        user = self._get_user(kwargs.get("user_id"))
        audio = request.FILES.get('audio')
        if not audio:
            raise ValidationError("Audio is required to upload.")
        verify_audio(audio)
        if not request.data.get('audio_type'):
            request.data['audio_type'] = choices.GENERIC
        request.data.update({'title': audio.name})
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.update({
            'content_object': user,
        })

        try:
            audio = Audio.objects.create(**serializer.validated_data)
        except Exception as e:
            raise e

        serialied_audio = self.get_serializer(audio)
        return Response(serialied_audio.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """List all audios uploaded by user."""
        user = self._get_user(kwargs.get("user_id"))
        queryset = user.audios.all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
