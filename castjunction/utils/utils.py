"""utitly methods and classes for the project."""

from datetime import datetime, timedelta
from collections import OrderedDict
from functools import wraps


from django.utils.decorators import available_attrs
from django.contrib.auth.views import redirect_to_login

from rest_framework import serializers

from users.models import Bio
from users.utils import is_user_casting_director

from pinax.referrals.models import Referral

VIDEO_THUMBNAIL_GENERATOR = "ffmpeg -ss 1 -i {0} -frames:v 1 {1}/thumb%02d.jpg"

VALID_ACTIONS = [
    "RESPONDED",
    "STAGE_ROUTE_UNPAID",
    "STAGE_ROUTE_PAID",
    "CASTING_DIRECTOR_UNPAID",
    "CASTING_DIRECOR_PAID",
]


class ChoicesField(serializers.Field):
    """Custom ChoiceField serializer field."""

    def __init__(self, choices, **kwargs):
        """init."""
        self._choices = OrderedDict(choices)
        super(ChoicesField, self).__init__(**kwargs)

    def to_representation(self, obj):
        """Used while retrieving value for the field."""
        return self._choices[obj]

    def to_internal_value(self, data):
        """Used while storing value for the field."""
        for i in self._choices:
            if self._choices[i] == data:
                return i
        raise serializers.ValidationError(
            "Acceptable values are {0}.".format(list(self._choices.values()))
        )


def create_referral(user):
    """Generate referrel code for this user."""
    return Referral.create(user=user, redirect_to="/")


def get_referrer_user(request, user=None):
    """Get referrer user."""
    code = request.data.get("referral_code")
    action = request.data.get("medium")
    if action and action not in VALID_ACTIONS:
        action = "RESPONDED"
    if code:
        try:
            referral_obj = Referral.objects.get(code=code)
        except Referral.DoesNotExist:
            return None
        referrer_user = referral_obj.user
        if not action:
            if is_user_casting_director(referrer_user):
                action = "CASTING_DIRECTOR_UNPAID"
            elif referrer_user.is_admin:
                action = "STAGE_ROUTE_UNPAID"
            else:
                action = "RESPONDED"
        if not request.session.exists(request.session.session_key):
            request.session.create()
        referral_obj.respond(request, action, user=user, target=referrer_user)
        # incentives for this user
        return referrer_user


def check_person_information(user):
    """Check for fields of user and if they are not filled return False."""
    result = {
        "skills": True,
        "known_languages": False,
        "bio": True,
        "educations": True,
        "experiences": True,
        "images": False,
        "videos": True,
    }
    if user.skills.count() > 0:
        result["skills"] = True
    if user.known_languages.count() > 0:
        result["known_languages"] = True
    if user.images.count() > 0:
        result["images"] = True
    try:
        user.bio
        bio_fields = [
            "hair_color",
            "eye_color",
            "height",
            "waist",
            "shoulders",
            "shoe_size",
        ]

        for field in bio_fields:
            if not getattr(user.bio, field):
                result["bio"] = False
                break
    except Bio.DoesNotExist:
        result["bio"] = False

    return result


def last_day_of_month(date):
    """Return last date of input date's month."""
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - timedelta(days=1)


def string_to_date(date_string):
    """Convert string to date."""
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except Exception as e:
        raise e


def group_required(group_names):
    """group_name will be the list of group name."""

    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def inner(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated():
                if (
                    user.groups.filter(name__in=group_names) and user.is_staff
                ) or user.is_superuser:
                    return func(request, *args, **kwargs)
                return redirect_to_login("/admin/")

        return inner

    return decorator


def dump(qs, outfile_path):
    """
    Take in a Django queryset and spits out a CSV file.

    Usage::

        >> from utils.utils import dump
        >> qs = <your_query>
        >> dump(qs, '<path/to/csv/file/')

    Based on a snippet by zbyte64::

        http://www.djangosnippets.org/snippets/790/

    """
    import csv

    model = qs.model
    writer = csv.writer(open(outfile_path, "w"))

    headers = []
    for field in model._meta.fields:
        headers.append(field.name)
    writer.writerow(headers)

    for obj in qs:
        row = []
        for field in headers:
            val = getattr(obj, field)
            if callable(val):
                val = val()
            # if isinstance(val, unicode):
            #     val = val.encode("utf-8")
            row.append(val)
        row.append(obj.images.count())
        writer.writerow(row)
