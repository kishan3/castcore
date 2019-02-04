"""Notification classes."""
# -*- coding: utf-8 -*-

from django.template import loader
from django.conf import settings as django_settings

from .tasks import send_mail, send_mass_html_mail


class Notification(object):
    """Base class for all Notification objects."""

    body = None
    subject = None

    def __init__(self, body, subject, *args, **kwargs):
        """Initialize the body and subject for the notification object."""
        if not body:
            raise ValueError("Empty body specified for notification.")
        self.body = body
        self.subject = subject

    def send(self):
        """Method to send out the notification."""
        raise NotImplementedError("To be implemented in derived class.")


class EmailNotification(Notification):
    """Notification class for Email messages/notifications."""

    body_template_path = None
    subject_template_path = None
    cc = None
    bcc = None

    def __init__(self, receiver, sender=None, is_template=False, body_template_path=None, subject_template_path=None, *args, **kwargs):
        """Initialize required attributes for sending out mail."""
        if sender is None:
            sender = getattr(django_settings, 'STAGEROUTE_EMAIL', None)
        if sender is None or receiver is None:
            raise ValueError("Email sender and recipient required.")

        kwargs['context'] = self._set_default_email_context(kwargs.pop('context', {}))
        if is_template:
            kwargs['body'], kwargs['subject'] = self._create_from_template(kwargs['context'])
        super().__init__(*args, **kwargs)
        self.sender = sender
        if kwargs.get('cc'):
            self.cc = kwargs.get('cc')
        if kwargs.get('bcc'):
            self.bcc = kwargs.get('bcc')
        if not isinstance(receiver, list):
            receiver = [receiver]
        self.receivers = receiver

    def _create_from_template(self, context=None):
        if self.body_template_path is None or self.subject_template_path is None:
            raise ValueError("Template paths have not been specified.")
        body = loader.render_to_string(self.body_template_path, context)
        subject = loader.render_to_string(self.subject_template_path, context)
        subject = ''.join(subject.splitlines())

        return body, subject

    def send(self):
        """Send out mail using the send_mail task."""
        send_mail.delay(self.subject, self.body, self.sender, self.receivers,
                        self.cc, self.bcc, content_type='html',
                        class_name=self.__class__.__name__)

    def _set_default_email_context(self, context):
        context['assessment_site_name'] = getattr(django_settings, 'EMAIL_ASSESSMENT_SITE_NAME', None)
        context['MEDIA_URL'] = getattr(django_settings, 'MEDIA_URL', None)
        return context


class WelcomeEmailNotification(EmailNotification):
    """Email notification for sending out reset password link to user."""

    body_template_path = 'email/welcome_email_body.html'
    subject_template_path = 'email/welcome_email_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class ResetPasswordEmailNotification(EmailNotification):
    """Email notification for sending out reset password link to user."""

    body_template_path = 'email/password_reset_email_body.html'
    subject_template_path = 'email/password_reset_email_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class ReferralInvitationEmailNotification(EmailNotification):
    """Email notification for sending out referral invitations to users."""

    body_template_path = 'email/referral_invitation_body.html'
    subject_template_path = 'email/referral_invitation_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class JobInviteEmailNotification(EmailNotification):
    """Email notification for job invitation."""

    body_template_path = 'email/job_invited_email_body.html'
    subject_template_path = 'email/job_invited_email_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class JobShortlistedEmailNotification(EmailNotification):
    body_template_path = 'email/job_shortlisted_email_body.html'
    subject_template_path = 'email/job_shortlisted_email_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class ProfileViewedEmailNotification(EmailNotification):
    body_template_path = 'email/profile_viewed_email_body.html'
    subject_template_path = 'email/profile_viewed_email_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class JobApprovedEmailNotification(EmailNotification):
    body_template_path = 'email/job_approved_email_body.html'
    subject_template_path = 'email/job_approved_email_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)

    def send(self, **kwargs):
        """Send out mail using the mass_mail task."""
        messages = list()
        for receiver in self.receivers:
            messages.append([self.subject,
                             self.body,
                             self.sender,
                             [receiver],
                             ])
        tuple_of_messages = tuple(tuple(x) for x in messages)
        send_mass_html_mail(tuple_of_messages, fail_silently=False)


class VerifyEmailReminderNotification(EmailNotification):
    body_template_path = 'email/verify_email_reminder_body.html'
    subject_template_path = 'email/verify_email_reminder_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class NotifyUser(EmailNotification):
    """A generalised method for different notifications."""

    body_template_path = 'email/notify_user_body.html'
    subject_template_path = 'email/notify_user_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)


class ProfileApprovedEmailNotification(EmailNotification):
    body_template_path = 'email/profile_approved_email_body.html'
    subject_template_path = 'email/profile_approved_email_subject.txt'

    def __init__(self, receiver, sender=None, *args, **kwargs):
        """Initialize the required attributes."""
        super().__init__(receiver, sender, is_template=True, *args, **kwargs)
