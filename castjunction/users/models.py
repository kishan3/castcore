"""Models for user management."""
from __future__ import unicode_literals

from datetime import date, datetime
from cities.models import City, Country, PostalCode

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


from django_hstore import hstore
from select_multiple_field.models import SelectMultipleField

from utils import choices, mixins
from multimedia.models import Image, Video, Audio


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        """Create and saves a User with the given email and password."""
        if not email:
            raise ValueError('Email must be provided.')
        email = self.normalize_email(email)
        user = self.model(
            email=email, is_staff=is_staff, is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)


class SearchableField(models.Model):
    """Searchable fields for entire project."""

    model_name = models.CharField(
        max_length=255,
        help_text='model name on which search is performed.')
    field_name = models.CharField(
        max_length=255,
        help_text='field of the model on which search is performed.')
    value = models.CharField(
        max_length=255,
        help_text='Value for this field.')
    data = hstore.DictionaryField(null=True, blank=True)

    objects = hstore.HStoreGeoManager()

    def __str__(self):
        """Return field and its value."""
        return self.field_name.upper()+" "+self.value


class UserIncentives(mixins.CommonFieldsMixin):

    application = models.CharField(
        max_length=255,
        default="25%",
        help_text='Incentives for application on job post.')
    job_post = models.CharField(
        max_length=255,
        default="500",
        help_text='Incentives for job post.')
    user_paid = models.CharField(
        max_length=255,
        default="500",
        help_text='Incentives for user payment.')

    def __str__(self):
        """Return title of incetive plan."""
        return self.title


class PersonType(models.Model):
    """Person types for each user."""

    TALENT = 'talent'
    DIRECTOR = 'director'
    CASTING_DIRECTOR = 'casting_director'

    PERSON_TYPE_CHOICES = (
        (TALENT, 'Talent'),
        (DIRECTOR, 'Director'),
        (CASTING_DIRECTOR, 'Casting_Director'),
    )
    person_type = models.CharField(
        max_length=30,
        choices=PERSON_TYPE_CHOICES,
        blank=False,
        default=TALENT)

    def __str__(self):
        """Return type of person."""
        return self.person_type


@python_2_unicode_compatible
class User(AbstractBaseUser, PermissionsMixin):
    PERSON = 'P'
    COMPANY = 'C'

    USER_TYPE = (
        (PERSON, 'Person'),
        (COMPANY, 'Company'),
    )
    email = models.EmailField(_('email address'),
                              unique=True,
                              null=True,
                              db_index=True,
                              blank=True,
                              help_text='Should be valid email, e.g. name@example.com',)

    first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='First Name',
        help_text=_('John'),
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Last Name',
        help_text=_('Doe'),
    )

    user_type = models.CharField(max_length=1, choices=USER_TYPE, default=PERSON)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    phone = models.CharField(
        unique=True, max_length=10, null=True, blank=True,
        db_index=True, help_text=_("User's phone number."))
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text=_("This can be date of incorporation in case of house or company."))

    nationality = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        help_text=_("This will be location of head office in case of production house or company."))
    city = models.ForeignKey(
        City,
        null=True,
        blank=True,
        related_name='city',
        help_text=_("City where user or company resides."))

    email_daily_updates = models.BooleanField(
        default=False,
        help_text='Whether to mail updates daily?')

    sms_passcode = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Passcode for user\'s phone verification'
    )

    is_email_verified = models.BooleanField(
        default=False,
        verbose_name='Email of user is verified?')
    is_phone_verified = models.BooleanField(
        default=False,
        help_text='Phone number of user is verified?')
    is_profile_approved = models.BooleanField(
        default=False,
        help_text='Profile of user is approved by StageRoute?')
    profile_completion_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text="How much percentage user's profile is filled.")
    stageroute_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(5)],
        help_text='StageRoute ranking for the user.'
    )
    interested_professions = SelectMultipleField(
        max_length=50,
        default=choices.OTHER,
        choices=choices.JOB_TYPE_CHOICES)

    @property
    def is_admin(self):
        return self.is_staff or self.is_superuser

    @property
    def age(self):
        today = date.today()
        born = self.date_of_birth
        if not born:
            return None
        try:
            birthday = born.replace(year=today.year)
        # raised when birth date is February 29 and the current year is not a
        # leap year
        except ValueError:
            birthday = born.replace(year=today.year, month=born.month+1, day=1)
        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year

    objects = UserManager()
    USERNAME_FIELD = 'email'

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if not self.phone:
            self.phone = None
        if not self.email:
            self.email = None

    def __str__(self):
        """Return email or first_name."""
        return self.email or self.first_name

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class Person(User):
    typ = models.ManyToManyField(
        PersonType, related_name='persons', related_query_name='person')
    gender = models.CharField(
        max_length=2,
        db_index=True,
        default=choices.NOT_SPECIFIED,
        choices=choices.GENDER_CHOICES)
    images = GenericRelation(Image, related_query_name='person')
    videos = GenericRelation(Video, related_query_name='person')
    audios = GenericRelation(Audio, related_query_name='person')
    associated_with_agent = models.BooleanField(
        default=False,
        help_text='Whether user has agents working for him/her?')
    incentive_plan = models.ForeignKey(
        UserIncentives,
        null=True,
        blank=True,
        help_text='Incentive plan details.')

    def clean(self):
        if not self.phone:
            self.phone = None
        if not self.email:
            self.email = None


class Skill(models.Model):
    skill_name = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    person = models.ManyToManyField(
        Person, related_name='skills', related_query_name='skill')


class Bio(models.Model):
    """Bio stores physical attributes and contact details for user."""

    person = models.OneToOneField(Person,
                                  related_name='bio',
                                  related_query_name='bio',
                                  on_delete=models.CASCADE)

    # hstore field for storing person's physical attributes.
    # http://djangonauts.github.io/django-hstore/#_python_api
    data = hstore.DictionaryField(schema=[
        {
            'name': 'street_address',
            'class': 'CharField',
            'kwargs': {
                'blank': True, 'max_length': 255, 'null': True,
            }
        },
        {
            'name': 'hair_color',
            'class': 'CharField',
            'kwargs': {
                'default': 'Black', 'blank': True, 'max_length': 20, 'null': True,
                'choices': (
                    ("black", "black"),
                    ("dark_brown", "dark_brown"),
                    ("light_brown", "light_brown"),
                    ("blonde", "blonde"),
                    ("red", "red"),
                    ("grey", "grey"),
                    ("white", "white"),
                    ('does_not_matter', ''),
                )

            }
        },
        {
            'name': 'eye_color',
            'class': 'CharField',
            'kwargs': {
                'blank': True, 'max_length': 20, 'null': True,
                'choices': (
                    ("black", "black"), ("blue", "blue"),
                    ("dark_brown", "dark_brown"),
                    ("light_brown", "light_brown"),
                    ("green", "green"), ("grey", "grey"),
                    ("violet", "violet"), ("hazel", "hazel"),
                    ('does_not_matter', ''),
                )
            },

        },
        {
            'name': 'height',
            'class': 'FloatField',
            'kwargs': {
                'blank': True, 'null': True,
            }
        },
        {
            'name': 'waist',
            'class': 'IntegerField',
            'kwargs': {
                'blank': True, 'null': True,
            }
        },
        {
            'name': 'shoulders',
            'class': 'IntegerField',
            'kwargs': {
                'blank': True, 'null': True,
            }
        },
        {
            'name': 'chest',
            'class': 'IntegerField',
            'kwargs': {
                'blank': True, 'null': True,
            }
        },
        {
            'name': 'hips',
            'class': 'IntegerField',
            'kwargs': {
                'blank': True, 'null': True,
            }
        },
        {
            'name': 'shoe_size',
            'class': 'FloatField',
            'kwargs': {
                'blank': True, 'null': True,
            }
        },
        {
            'name': 'hair_style',
            'class': 'CharField',
            'kwargs': {
                'blank': True, 'max_length': 50, 'null': True,
                'choices': (
                    ("army_cut", "army_cut"), ("normal", "normal"),
                    ("slightly_long", "slightly_long"),
                    ("shoulder_length", "shoulder_length"),
                    ("partially_bald", "partially_bald"),
                    ("completely_bald", "completely_bald"),
                    ("boy_cut", "boy_cut"), ("bust_length", "bust_length"),
                    ("waist_length", "waist_length"),
                    ("knee_length", "knee_length"),
                    ('does_not_matter', '')
                )
            }
        },
        {
            'name': 'hair_type',
            'class': 'CharField',
            'kwargs': {
                'blank': True, 'max_length': 50, 'null': True,
                'choices': (
                    ('straight', 'straight'), ('wavy', 'wavy'),
                    ('curly', 'curly'), ('bald', 'bald'),
                    ('half_bald', 'half_bald'), ('scanty', 'scanty'),
                    ('does_not_matter', '')
                )
            }
        },
        {
            'name': 'skin_type',
            'class': 'CharField',
            'kwargs': {
                'blank': True, 'max_length': 50, 'null': True,
                'choices': (
                    ("very_fair", "very_fair"), ("fair", "fair"),
                    ("wheatish", "wheatish"), ("dusky", "dusky"),
                    ("dark", "dark"), ("very_dark", "very_dark"),
                    ('does_not_matter', '')
                )
            }
        },
        {
            'name': 'body_type',
            'class': 'CharField',
            'kwargs': {
                'blank': True, 'max_length': 50, 'null': True,
                'choices': (
                    ('skinny', 'skinny'), ('bulky', 'bulky'),
                    ('slim', 'slim'), ('athletic', 'athletic'),
                    ('muscular', 'muscular'), ('curvy', 'curvy'),
                    ('heavy', 'heavy'),
                    ('very_heavy', 'very_heavy'),
                    ('very_fat', 'very_fat'),
                    ('does_not_matter', '')
                )
            }
        },


    ],
        db_index=True
    )

    zipcode = models.ForeignKey(
        PostalCode,
        null=True,
        blank=True)

    objects = hstore.HStoreManager()


class Language(models.Model):
    """This stores Language that can be linked with multiple users."""

    language_name = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    person = models.ManyToManyField(
        Person,
        related_name='known_languages',
        related_query_name='known_language')


class Institute(models.Model):
    institute_name = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    established_year = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when institute was established."))
    location = models.ForeignKey(
        City,
        null=True,
        blank=True,
        related_name='institute_cities',
        help_text=_("Location of institute."))

    def __str__(self):
        """Return institute name."""
        return self.institute_name


class Education(models.Model):

    related_name = 'educations'
    related_query_name = 'education'

    person = models.ForeignKey(
        Person,
        related_name=related_name,
        related_query_name=related_query_name)

    institute = models.ForeignKey(
        Institute,
        related_name=related_name,
        related_query_name=related_query_name)

    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when person started the course."))
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when person ended the course."))
    degree = models.CharField(
        max_length=255,
        null=True, blank=True, db_index=True,
        help_text=_("Educational degree for e.g BTech, M.sc, B.Com etc."))
    grade = models.CharField(
        max_length=20,
        null=True, blank=True,
        help_text=_("Grade for e.g A+, B+, first class , distinction etc."))
    field_of_study = models.CharField(
        max_length=50,
        null=True,
        db_index=True,
        blank=True,
        help_text=_('In which stream of course degree was achieved.'))
    social_activites = models.TextField(
        null=True, blank=True,
        help_text=_("Description about user's extracurricular and other social activites."))
    description = models.TextField(
        null=True, blank=True,
        help_text=_("Description for user's Education in detail."))

    @property
    def degree_completed(self):
        if self.end_date and (self.end_date < datetime.today()):
            return True
        else:
            return False


class Experience(models.Model):

    FEATURE_FILM = 1
    TVSHOW = 2
    ADVERTISEMENT = 3
    THEATRE = 4
    MODELLING = 5
    OTHERS = 5

    EXPERIENCE_TYPE = (
        (FEATURE_FILM, 'Feature Film'),
        (TVSHOW, 'Tv show'),
        (ADVERTISEMENT, 'Advertisement'),
        (THEATRE, 'Theatre'),
        (MODELLING, 'Modelling'),
        (OTHERS, 'Others'),
    )

    person = models.ForeignKey(
        Person,
        related_name='experiences',
        related_query_name='experience')

    production_house = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(
        max_length=255, null=True, blank=True,
        help_text='Name for the project experience for ex. Sherlock Holmes.')
    role = models.CharField(
        max_length=255, null=True, blank=True,
        help_text='For eg. lead character, supporting character, background dancer etc.')
    character_name = models.CharField(
        max_length=255, null=True, blank=True,
        help_text='Name of character.')
    experience_type = models.PositiveSmallIntegerField(
        choices=EXPERIENCE_TYPE,
        null=True,
        blank=True)

    location = models.ForeignKey(City,
                                 null=True,
                                 blank=True,
                                 help_text=_("Location of user's project experience."))

    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when person started the course."))
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when person ended the course."))
    description = models.TextField(
        null=True, blank=True,
        help_text=_("Desctiption about user's experience."))


class CompanyType(models.Model):
    PRODUCTION_HOUSE = 'production_house'
    COMPANY_TYPE_CHOICES = (
        (PRODUCTION_HOUSE, 'production house'),
    )
    company_type = models.CharField(
        choices=COMPANY_TYPE_CHOICES,
        max_length=30,
        blank=False,
        default=PRODUCTION_HOUSE)

    def __str__(self):
        """Return company type."""
        return self.company_type


class Bank(models.Model):
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Name of bank.')
    branch = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Branch of bank company is associated.')
    account_number = models.CharField(
        max_length=50,
        null=True,
        blank=True)
    ifsc_code = models.CharField(
        max_length=20,
        null=True,
        blank=True)
    pan_number = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text='Pan card number of company.')


class Company(User):
    """Company can be any production companys, musics studio, film studio etc."""

    related_name = 'companies'
    related_query_name = 'company'
    typ = models.ManyToManyField(
        CompanyType, related_name=related_name)
    members = models.ManyToManyField(
        Person, related_name=related_name, related_query_name=related_query_name)
    company_email = models.EmailField(
        _('email address'), null=True, blank=True)
    company_phone = models.CharField(
        unique=True, max_length=10, null=True, blank=True, help_text=_("Company's phone number object."))
    company_website = models.URLField(null=True, blank=True)
    bank = models.ForeignKey(
        Bank,
        null=True,
        blank=True,
        help_text='Bank details for the company.')

    images = GenericRelation(Image, related_query_name=related_query_name)
    videos = GenericRelation(Video, related_query_name=related_query_name)
    audios = GenericRelation(Audio, related_query_name=related_query_name)


class UserPreference(models.Model):
    user = models.OneToOneField(
        User,
        primary_key=True,
        related_name='preferences',
        related_query_name='preference',
        on_delete=models.CASCADE)

    app_notification = models.BooleanField(default=True)
    push_notification = models.BooleanField(default=True)
    sms_notification = models.BooleanField(default=True)
    email_notification = models.BooleanField(default=True)

    profile_state = models.CharField(
        choices=choices.PROFILE_STATE_CHOICES,
        max_length=2,
        default=choices.PUBLIC,
        help_text='Profile states of user.')
    search_preference = JSONField(null=True, blank=True)
