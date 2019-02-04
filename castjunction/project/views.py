"""Views for projects and jobs."""

from datetime import timedelta
from rest_framework import viewsets, mixins
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated,
                                        DjangoObjectPermissions,
                                        AllowAny)
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from rest_framework_extensions.decorators import link
from rest_framework import filters

from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Case, When, IntegerField
from django.db.models import Q

from users.models import User
from pinax.likes.models import Like
from multimedia.serializers import ImageSerializer
from multimedia.models import Image
from multimedia.utils import verify_image

import django_filters
from .models import Job
from .serializers import JobSerializer, JobDetailSerializer
from .utils import states_for_popular_jobs

from psycopg2.extras import NumericRange
from datetime import datetime
from users.views import LikeViewSet
from utils import choices


class JobFilter(django_filters.FilterSet):
    ages = django_filters.MethodFilter()
    budgets = django_filters.MethodFilter()
    heights = django_filters.MethodFilter()
    location = django_filters.MethodFilter()
    job_type = django_filters.MethodFilter()
    required_gender = django_filters.MethodFilter()
    body_type = django_filters.MethodFilter()
    eye_color = django_filters.MethodFilter()
    language = django_filters.MethodFilter()
    hair_type = django_filters.MethodFilter()
    skin_type = django_filters.MethodFilter()
    status = django_filters.MethodFilter()

    class Meta:
        model = Job

    def filter_language(self, queryset, value):
        if value:
            values = value.split(",")
            queryset = queryset.filter(Q(language__in=values) | Q(language=None))
        return queryset

    def filter_job_type(self, queryset, value):
        if value:
            values = value.split(",")
            queryset = queryset.filter(job_type__in=values)
        return queryset

    def filter_required_gender(self, queryset, value):
        if value:
            values = value.split(",")
            values.append("NS")
            queryset = queryset.filter(required_gender__in=values)
        return queryset

    def filter_body_type(self, queryset, value):
        if value:
            values = value.split(",")
            queryset = queryset.filter(Q(body_type__in=values) | Q(body_type=None))
        return queryset

    def filter_eye_color(self, queryset, value):
        if value:
            values = value.split(",")
            queryset = queryset.filter(Q(eye_color__in=values) | Q(eye_color=None))
        return queryset

    def filter_hair_type(self, queryset, value):
        if value:
            values = value.split(",")
            queryset = queryset.filter(Q(hair_type__in=values) | Q(hair_type=None))
        return queryset

    def filter_skin_type(self, queryset, value):
        if value:
            values = value.split(",")
            queryset = queryset.filter(Q(skin_type__in=values) | Q(skin_type=None))
        return queryset

    def filter_status(self, queryset, value):
        if value:
            if value == choices.APPROVED:
                queryset = queryset.filter(
                    status=value,
                    submission_deadline__gte=datetime.today())
            elif value == choices.CLOSED:
                queryset = queryset.filter(
                    status=choices.APPROVED,
                    submission_deadline__lte=datetime.today())
            else:
                queryset = queryset.filter(status=value)

        return queryset

    def filter_location(self, queryset, value):
        if value:
            values = value.split(",")
            queryset = queryset.filter(location__name_std__in=values)
        return queryset

    def filter_ages(self, queryset, value):
        if value:
            values = value.split(",")
            age_range = [int(age) for age in values if age is not '']
            if values[0] == '':
                # only max age is given
                queryset = queryset.filter(
                    ages__overlap=NumericRange(0, age_range[0]))
            elif values[1] == '':
                # only min age is given
                queryset = queryset.filter(
                    ages__overlap=NumericRange(age_range[0], None))
            elif len(age_range) == 2:
                # min age and max age given
                queryset = queryset.filter(ages__overlap=NumericRange(age_range[0], age_range[1]))
            else:
                raise ValidationError("Please provide only two ages for filter.")

        return queryset

    def filter_budgets(self, queryset, value):
        if value:
            values = value.split(",")
            budget_range = [int(budget) for budget in values if budget is not '']
            if values[0] == '':
                # only max budget is given
                queryset = queryset.filter(
                    budgets__overlap=NumericRange(0, budget_range[0]))
            elif values[1] == '':
                # only min budget is given
                queryset = queryset.filter(
                    budgets__overlap=NumericRange(budget_range[0], None))

            elif len(budget_range) == 2:
                # min budget and max budget given
                queryset = queryset.filter(
                    budgets__overlap=NumericRange(budget_range[0], budget_range[1]))
            else:
                raise ValidationError("Please provide only two budget values for filter.")

        return queryset

    def filter_heights(self, queryset, value):
        if value:
            values = value.split(",")
            height_range = [int(height) for height in values if height is not '']
            if values[0] == '':
                # only max height is given
                queryset = queryset.filter(
                    heights__overlap=NumericRange(0, height_range[0]))
            elif values[1] == '':
                # only min height is given
                queryset = queryset.filter(
                    heights__overlap=NumericRange(height_range[0], None))
            elif len(height_range) == 2:
                # min height and max height given
                queryset = queryset.filter(
                    heights__overlap=NumericRange(height_range[0], height_range[1]))
            else:
                raise ValidationError("Please provide only two height values for filter.")

        return queryset


class JobViewSet(viewsets.ModelViewSet):
    """Create, Update and retrieve jobs."""

    queryset = Job.objects.all()
    exclude_fields = ['location', 'group']
    serializer_class = JobSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter,)
    filter_class = JobFilter
    search_fields = ("title", "role_position", "location__slug")

    def __init__(self, **kwargs):
        """Init method."""
        self._data = {}
        super().__init__(**kwargs)

    def get_permissions(self):
        if self.request.method == 'POST':
            return (DjangoObjectPermissions(), )
        return (IsAuthenticatedOrReadOnly(), )

    def get_serializer(self, *args, **kwargs):
        if self.request.user.is_anonymous():
            kwargs.update({'exclude_fields': self.exclude_fields})
            return self.serializer_class(context={'request': self.request}, *args, **kwargs)
        else:
            return self.serializer_class(context={'request': self.request}, *args, **kwargs)

    def get_user(self):
        """Get user to authenticate."""
        if 'user' not in self._data:
            self._data['user'] = User.objects.get(pk=self.kwargs['user_id'])
        return self._data['user']

    def get_queryset(self):
        """Return all approved jobs."""
        jobs = Job.objects.all()
        if not self.kwargs.get('pk'):
            jobs = jobs.filter(
                status=choices.APPROVED,
                submission_deadline__gte=datetime.today()).order_by('-created_at')
            if not self.request.user.is_anonymous():
                # if user is logged in, exclude his/her applied jobs.
                # also append ignored jobs at the end of job listing.
                jobs = jobs.exclude(~Q(application__state='ignored'),
                                    application__user=self.request.user).order_by('-created_at')

                if self.request.user.user_type == User.PERSON:
                    # If user is of type "person",
                    # show only jobs related to his/her gender along with not_specified jobs.
                    if self.request.user.person.gender != "NS":
                        jobs = jobs.filter(
                            required_gender__in=[self.request.user.person.gender,
                                                 choices.NOT_SPECIFIED])
        return jobs

    def create(self, request, *args, **kwargs):
        """Create and store image if present."""
        if (request.data.get("audition_range")):
            if not (request.data['audition_range'].get('lower') and request.data['audition_range'].get('upper')):
                raise ValidationError("Audition date range upper and lower both needed.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("audition_range"):
            sub_dead = serializer.validated_data['audition_range'].upper - timedelta(days=1)
            serializer.validated_data.update({"submission_deadline": sub_dead})
        job = serializer.save()

        image = request.FILES.get('image')
        if image:
            image_data = {'image': image}
            verify_image(image)
            image_data.update({'title': image.name})
            image_type = request.data.get('image_type', 'Generic')
            image_data.update({'image_type': image_type})
            image_serializer = ImageSerializer(data=image_data)
            image_serializer.is_valid(raise_exception=True)
            image_serializer.validated_data.update({
                'content_object': job,
            })
            try:
                image = Image.objects.create(**image_serializer.validated_data)
            except Exception as e:
                raise e
        return Response(serializer.data)

    @link(permission_classes=[IsAuthenticated], is_for_list=True)
    def likes(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        likes = Like.objects.filter(
            sender=self.request.user,
            receiver_content_type=ContentType.objects.get_for_model(Job)
        ).values_list('receiver_object_id', flat=True)
        queryset = queryset.filter(id__in=likes)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @link(permission_classes=[AllowAny], is_for_list=True)
    def featured(self, request, *args, **kwargs):
        queryset = Job.objects.filter(
            featured=True,
            status=choices.APPROVED,
            submission_deadline__gte=datetime.today()).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @link(permission_classes=[AllowAny], is_for_list=True)
    def popular(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # refere this for explaination of following query
        # https://docs.djangoproject.com/en/dev/ref/models/conditional-expressions/#conditional-expressions
        ordered = queryset.annotate(
            app=Sum(
                Case(
                    When(application__state__in=states_for_popular_jobs, then=1),
                    default=0,
                    output_field=IntegerField())
            )).order_by("-app")
        page = self.paginate_queryset(ordered)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(ordered, many=True)
        return Response(serializer.data)

    @link(permission_classes=[AllowAny], is_for_list=True)
    def vendors(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())[:25]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class JobLikeViewSet(LikeViewSet):
    """User related like view set."""

    def get_queryset(self):
        return super(JobLikeViewSet, self).get_queryset().filter(
            receiver_content_type=ContentType.objects.get_for_model(Job)
        )

    def create(self, request, *args, **kwargs):
        """Create user."""
        contenttype = ContentType.objects.get_for_model(Job)
        try:
            obj, liked = Like.like(request.user, contenttype, kwargs.get('parent_lookup_receiver_object_id'))
            return Response({'liked': liked,
                            'id': obj.receiver_object_id
                             })
        except APIException as api_error:
            return ValidationError(api_error.details)


class UserJobsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Get all jobs posted by user."""

    serializer_class = JobDetailSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = JobFilter
    ordering_fields = ('created_at',)
    ordering = ('-created_at',)

    def get_queryset(self):
        return Job.objects.filter(created_by=self.request.user)
