"""Utility methods for user management."""
from django.contrib.auth.tokens import default_token_generator

from django.conf import settings as django_settings

from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text

from .models import User, PersonType, UserIncentives

PERCENTAGE_BASIC_DETAILS_FIELDS = {"first_name": 5,
                                   "gender": 5,
                                   "nationality": 2,
                                   "date_of_birth": 5,
                                   "city": 2}

PERCENTAGE_PROFILE_FIELDS = {"experiences": 10,
                             "educations": 5,
                             "skills": 5,
                             "known_languages": 4,
                             "images": 5,
                             "extra_multimedia": 10,
                             "phone_verified": 5,
                             "email_verified": 5,
                             "bio": 15,
                             }


def generate_code(referral_class):
    """Generate referral code for user."""
    def _generate_code():
        return get_random_string(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                                          '0123456789')
    code = _generate_code()
    while referral_class.objects.filter(code=code).exists():
        code = _generate_code()
    return code


def encode_uid(pk):
    """Encode pk."""
    return urlsafe_base64_encode(force_bytes(pk)).decode()


def decode_uid(pk):
    """Decode pk."""
    return force_text(urlsafe_base64_decode(pk))


def get_email_context(user):
    """Return url to send in email."""
    token = default_token_generator.make_token(user)
    uid = encode_uid(user.pk)
    domain = django_settings.DOMAIN
    site_name = django_settings.EMAIL_DEFAULT_SITE_NAME
    return {
        'user': user,
        'domain': domain,
        'site_name': site_name,
        'uid': uid,
        'token': token,
        'protocol': 'http',
    }


def is_user_casting_director(user):
    """Return true if user is casting_director."""
    if user.user_type == User.PERSON:
        if user.person.typ.filter(person_type=PersonType.CASTING_DIRECTOR):
            return True
    return False


def get_user_incentive_plan(user):
    """Get incentive plan of user. If no plan return default plan."""
    incentive_plan = user.person.incentive_plan
    if not incentive_plan:
        incentive_plan, created = UserIncentives.objects.get_or_create(title="default")
    return incentive_plan


def get_incetive_amount(incentive_plan, field, total_amount=None):
    """Return the amount to credit."""
    value = getattr(incentive_plan, field)
    if value.endswith("%"):
        try:
            value = int(value.split('%')[0])
        except Exception as e:
            raise e
        incentive_amount = total_amount * (value/100)
    # if not % its a direct value to credit to CA
    else:
        try:
            incentive_amount = int(value)
        except Exception as e:
            raise e
    return incentive_amount


def update_users_profile_percentage(user, field_name):
    """Update user's profile completion percentage."""
    percentage = None
    if user.user_type == 'P':
        if getattr(user.person, field_name).count() == 0:
            percentage = user.profile_completion_percentage + PERCENTAGE_PROFILE_FIELDS[field_name]
    if percentage:
        User.objects.filter(id=user.id).update(profile_completion_percentage=percentage)


def increase_percentage(user, field_name):
    """Update user's profile completion percentage."""
    percentage = user.profile_completion_percentage + PERCENTAGE_PROFILE_FIELDS[field_name]

    User.objects.filter(id=user.id).update(profile_completion_percentage=percentage)
