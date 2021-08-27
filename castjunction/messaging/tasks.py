"""Message related tasks."""
import urllib

from django_rq import job
from django.core.mail import EmailMessage
from django.core.mail import get_connection
from django.conf import settings as django_settings

from actstream import action


@job("default")
def send_mail(
    subject,
    body,
    sender,
    receivers,
    cc=None,
    bcc=None,
    content_type="plain",
    class_name=None,
):
    """Send email to users."""
    try:
        # Send email
        email_message = EmailMessage(subject, body, sender, receivers, cc=cc, bcc=bcc)
        email_message.content_subtype = content_type
        email_message.send()
        return "%s has been sent" % class_name
    except Exception as e:
        raise e


@job("default")
def send_mass_html_mail(
    datatuple, fail_silently=False, user=None, password=None, connection=None
):
    """Given a datatuple of (subject, text_content, html_content, from_email.

    recipient_list), sends each message to each recipient list. Returns the
    number of emails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.
    """
    connection = connection or get_connection(
        username=user, password=password, fail_silently=fail_silently
    )
    messages = []
    for subject, text, from_email, recipient in datatuple:
        message = EmailMessage(subject, text, from_email, recipient)
        message.content_subtype = "html"
        messages.append(message)
    return connection.send_messages(messages)


def send_push_notification(user, message, **kwargs):
    """Send push notification to user."""
    from push_notifications.models import GCMDevice

    if user.preferences.push_notification:
        try:
            device = GCMDevice.objects.get(user=user)
            device.send_message(message, **kwargs)
        except GCMDevice.DoesNotExist:
            pass
    else:
        pass


@job("default")
def bulk_send_push_notification(users, message, **kwargs):
    """Send push notification to user."""
    from push_notifications.models import GCMDevice

    try:
        devices = GCMDevice.objects.filter(user__in=users, active=True)
        devices.send_message(message, **kwargs)
    except GCMDevice.DoesNotExist:
        pass


def send_app_notification(sender, verb, action_object, target, description):
    """Send app notification to user."""
    try:
        action.send(
            sender,
            verb=verb,
            action_object=action_object,
            target=target,
            description=description,
        )
    except Exception as e:
        raise e


def send_sms(phone, message):
    """Send OTP to user."""
    user_phone_data = {
        "username": django_settings.SMS_USERNAME,
        "password": django_settings.SMS_PASSWORD,
        "type": django_settings.SMS_TYPE,
        "sender": django_settings.SMS_SENDER,
        "mobile": phone,
        "message": message,
    }

    encoded_user_phone_data = urllib.parse.urlencode(user_phone_data)
    # binary_data = encoded_user_phone_data.encode('utf-8')

    try:
        response = urllib.request.urlopen(
            url=django_settings.SMS_API_URL + "?" + encoded_user_phone_data
        )
    except Exception as e:
        raise e
    return response
