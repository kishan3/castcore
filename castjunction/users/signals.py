"""signals for users app."""
import django_rq
from datetime import datetime, timedelta

from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings as django_settings

from actstream import action
from actstream.models import Action

from allauth.account.signals import user_signed_up

from messaging.mails import (
    WelcomeEmailNotification,
    VerifyEmailReminderNotification,
    ProfileApprovedEmailNotification,
)
from messaging.tasks import send_sms
from messaging.messages import (
    SMS_ON_SIGN_UP,
    REMINDER_VERIFY_PHONE_SMS,
    EMAIL_PASSWORD_LINE,
    SMS_ON_SIGN_UP_WITH_PASSWORD,
)


from user_tokens.accounts_manager import create_limited_credit_account

from .utils import get_email_context, PERCENTAGE_BASIC_DETAILS_FIELDS
from .models import UserPreference, User


def send_verification_reminder_sms(user):
    """Remind signed up user to verify email."""
    # # check for his email preference.
    import django

    django.setup()
    from .models import User

    user = User.objects.get(id=user.id)
    if not user.is_phone_verified:
        send_sms(
            user.phone,
            REMINDER_VERIFY_PHONE_SMS.format(
                **{"otp_url": django_settings.DOMAIN + "/" + django_settings.OTP_URL}
            ),
        )
    return None


def send_verification_reminder_email(user):
    """Remind signed up user to verify email."""
    # # check for his email preference.
    import django

    django.setup()
    from .models import User

    user = User.objects.get(id=user.id)
    if not user.is_email_verified:
        context = get_email_context(user)
        context["first_name"] = user.first_name
        context["url"] = django_settings.ACTIVATION_URL.format(**context)
        VerifyEmailReminderNotification(user.email, context=context).send()
    return None


@receiver(user_signed_up, dispatch_uid="allauth.user_signed_up")
def user_signed_up_(request, user, **kwargs):
    """Send email only if user signed up by email."""
    percentage = 0
    for key in PERCENTAGE_BASIC_DETAILS_FIELDS.keys():
        if getattr(user, key) not in ["NS", None]:
            percentage += PERCENTAGE_BASIC_DETAILS_FIELDS[key]

    User.objects.filter(id=user.id).update(profile_completion_percentage=percentage)

    if user.email:
        context = get_email_context(user)
        if user.first_name:
            context["first_name"] = user.first_name
        else:
            context["first_name"] = None
        context["url"] = django_settings.ACTIVATION_URL.format(**context)
        if user._password:
            context["password_line"] = EMAIL_PASSWORD_LINE.format(
                **{"password": user._password}
            )
        WelcomeEmailNotification(user.email, context=context).send()
    if user.phone:
        if user._password:
            send_sms(user.phone, SMS_ON_SIGN_UP_WITH_PASSWORD)
        else:
            send_sms(user.phone, SMS_ON_SIGN_UP)


@receiver(post_save, dispatch_uid="user.create_token_account")
def create_token_account(sender, created, instance, **kwargs):
    """Create token account for new user."""
    list_of_models = ("Person", "Company")
    if sender.__name__ in list_of_models:
        if created:
            # create user's token and reimbursement accounts.
            create_limited_credit_account(
                user=instance, account_type=django_settings.TOKEN_ACCOUNT
            )
            create_limited_credit_account(
                user=instance, account_type=django_settings.REIMBURSEMENT_ACCOUNT
            )
            action.send(instance, verb=u"joined stageroute.")
            UserPreference.objects.create(user=instance)
        else:
            if not Action.objects.filter(
                target_object_id=instance.id,
                description="Updated Profile",
                timestamp__gte=datetime.now(tz=timezone.utc) - timedelta(minutes=2),
            ).exists():
                action.send(
                    instance,
                    verb=u"updated the profile.",
                    description=u"Updated Profile",
                )

            if instance.is_profile_approved and instance.preferences.email_notification:
                context = {"first_name": instance.first_name}
                ProfileApprovedEmailNotification(instance.email, context=context).send()


@receiver(post_save, dispatch_uid="user.remind_to_verify_email")
def remind_to_verify_email(sender, created, instance, **kwargs):
    """Send verify email for the new user."""
    list_of_models = ("Person", "Company")
    scheduler = django_rq.get_scheduler("default")
    if sender.__name__ in list_of_models:
        if created and instance.email:
            datetime = instance.date_joined + timedelta(days=5)
            scheduler.schedule(
                scheduled_time=datetime,
                func=send_verification_reminder_email,
                args=[instance],
                interval=432000,  # 5 days
                repeat=5,
            )


@receiver(post_save, dispatch_uid="user.remind_to_verify_phone")
def remind_to_verify_phone(sender, created, instance, **kwargs):
    """Send reminder sms for the new user."""
    list_of_models = ("Person", "Company")
    scheduler = django_rq.get_scheduler("default")
    if sender.__name__ in list_of_models:
        if created and instance.phone:
            datetime = instance.date_joined + timedelta(hours=6)
            scheduler.schedule(
                scheduled_time=datetime,
                func=send_verification_reminder_sms,
                args=[instance],
                interval=259200,  # 3 days
                repeat=5,
            )
