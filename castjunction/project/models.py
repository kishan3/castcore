"""Model class for projects."""
from django.db import models
from django_hstore import hstore
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import (IntegerRangeField,
                                            FloatRangeField, DateRangeField)

from field_history.tracker import FieldHistoryTracker

from utils.mixins import CommonFieldsMixin
from cities.models import City
from users.models import User
from multimedia.models import Image, Video, Audio
from utils import choices


class Group(CommonFieldsMixin):
    """Model for storing group of jobs."""

    start_date = models.DateField(
        null=True,
        blank=True,
        help_text='Start date of the project.')


class Job(CommonFieldsMixin):
    """Job post associated with project."""

    related_name = 'jobs'
    related_query_name = 'job'

    created_by = models.ForeignKey(
        User,
        db_index=True,
        related_name='created_jobs',
        related_query_name='created_job',
        on_delete=models.CASCADE)
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        related_name=related_name,
        related_query_name=related_query_name)

    applicants = models.ManyToManyField(
        User,
        through='application.Application',
        related_name=related_name,
        related_query_name=related_query_name)

    role_position = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text='For eg. lead character, supporting character, background dancer etc.')
    ages = IntegerRangeField(
        null=True,
        blank=True,
        help_text='Age range required for this role.')
    required_gender = models.CharField(
        max_length=2,
        choices=choices.GENDER_CHOICES,
        default=choices.NOT_SPECIFIED)
    required_tokens = models.IntegerField(
        default=5,
        help_text='How much tokens user needs to have to apply to this job.')
    location = models.ForeignKey(
        City,
        null=True,
        blank=True,
        help_text="Location of user's project experience.")
    required_information_to_apply = hstore.DictionaryField(null=True, blank=True)
    reason_for_rejection = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Reason why the job was rejected/unapproved by stageroute.')
    submission_deadline = models.DateField(
        null=True,
        blank=True,
        help_text='Date for the job deadline.')

    status = models.CharField(
        max_length=2, choices=choices.JOB_STATE_CHOICES, default=choices.PENDING_APPROVAL)
    number_of_vacancies = models.IntegerField(
        default=1,
        help_text='How many positions are open for this job.')
    budgets = IntegerRangeField(
        null=True,
        blank=True,
        help_text='budget range amount to be spent on the job.')
    featured = models.BooleanField(
        default=False,
        help_text='Is job featured.')
    skin_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=choices.DOES_NOT_MATTER,
        choices=choices.SKIN_TYPE_CHOICES,
        help_text='Preferred skin type.')
    hair_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=choices.DOES_NOT_MATTER,
        choices=choices.HAIR_TYPE_CHOICES,
        help_text='Preferred hair type.')
    eye_color = models.CharField(
        max_length=50,
        default=choices.DOES_NOT_MATTER,
        null=True,
        blank=True,
        choices=choices.EYE_COLOR_CHOICES,
        help_text='Peferred eye color.')
    hair_color = models.CharField(
        max_length=50,
        default=choices.DOES_NOT_MATTER,
        null=True,
        blank=True,
        choices=choices.HAIR_COLOR_CHOICES,
        help_text='Peferred eye color.')
    hair_style = models.CharField(
        max_length=50,
        default=choices.DOES_NOT_MATTER,
        null=True,
        blank=True,
        choices=choices.HAIR_STYLE_CHOICES,
        help_text='Peferred eye color.')
    heights = FloatRangeField(
        null=True,
        blank=True,
        help_text='Range of height required.')
    body_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=choices.DOES_NOT_MATTER,
        choices=choices.BODY_TYPES)
    language = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=choices.DOES_NOT_MATTER,
        choices=choices.LANGUAGE_CHOICES,
        help_text='Preferred languages.')

    job_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=choices.JOB_TYPE_CHOICES,
        help_text='Type of job.')
    auditions_per_day = models.IntegerField(
        null=True,
        blank=True,
        help_text='Number of auditions to do per day for this job.'
    )
    audition_range = DateRangeField(
        null=True,
        blank=True,
        help_text='Audition range')
    job_owner_email = models.EmailField(
        null=True,
        blank=True,
        help_text='Should be valid email, e.g. name@example.com',)
    job_owner_phone = models.CharField(
        max_length=10, null=True, blank=True,
        db_index=True, help_text="User's phone number.")
    notes = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Useful for job posters. A quick note they can refere later.")
    field_history = FieldHistoryTracker(['status'])
    related_query_name = 'jobs'

    images = GenericRelation(Image, related_query_name=related_query_name)
    videos = GenericRelation(Video, related_query_name=related_query_name)
    audios = GenericRelation(Audio, related_query_name=related_query_name)
    objects = hstore.HStoreManager()

    def __unicode__(self):
        """unicode."""
        return self.title


class Key(CommonFieldsMixin):
    """Keys for hstore field in Job model."""

    key_name = models.CharField(max_length=255, blank=False)
    key_type = models.CharField(max_length=255, blank=False)
    title_director_display = models.CharField(max_length=255)
