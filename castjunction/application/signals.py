"""signals for application app."""
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings as django_settings

from postman.api import pm_write

from actstream import action
from users.utils import (get_incetive_amount,
                         get_user_incentive_plan,
                         is_user_casting_director)
from messaging.tasks import send_push_notification, send_app_notification
from messaging.messages import JOB_SHORTLISTED_MESSAGE, JOB_INVITE_MESSAGE
from messaging.mails import JobShortlistedEmailNotification, JobInviteEmailNotification
from .models import Application, State
from .serializers import AuditionInviteSerializer

from user_tokens.accounts_manager import credit_to_reimbursement_account


@receiver(post_save, sender=Application)
def application_state_chaged(sender, created, instance, **kwargs):
    """Record activities of user."""
    if instance.state != State.INTIATED:
        action.send(instance.user,
                    verb=u"{}".format(instance.state),
                    action_object=instance,
                    target=instance.job)
    if instance.state == State.APPLIED:
        job_creator = instance.job.created_by
        casting_director = is_user_casting_director(job_creator)
        if casting_director:
            incentive_plan = get_user_incentive_plan(job_creator)
            total_amount = instance.job.required_tokens * django_settings.CREDIT_TOKEN_VALUE
            amount = get_incetive_amount(incentive_plan,
                                         "application",
                                         total_amount)
            credit_to_reimbursement_account(
                job_creator,
                amount,
                merchant_reference="application_{}".format(instance.id))

    if instance.state == State.SHORTLISTED:
        # send push notification
        extra_data = ({"extra": {"data": json.dumps({"job_id": instance.job.id})}})
        send_push_notification(instance.user,
                               JOB_SHORTLISTED_MESSAGE,
                               **extra_data)
        # send email notifications
        if instance.user.preferences.email_notification:
            context = {"first_name": instance.user.first_name,
                       "job": instance.job,
                       "url": django_settings.JOB_OPPORTUNITIES_URL,
                       "domain": django_settings.DOMAIN}
            JobShortlistedEmailNotification(instance.user.email, context=context).send()

    if instance.state == State.INVITED:
        data = instance._extra_data
        data.update({'applications': [instance.id]})
        audition_serializer = AuditionInviteSerializer(data=data)
        audition_serializer.is_valid(raise_exception=True)
        audition_serializer.save()
        # send message to user who applied to this job.
        subject = audition_serializer.validated_data.get('title')
        body = "Hi {}, {} at location {} on {}".format(
            instance.user.first_name,
            audition_serializer.validated_data['description'],
            audition_serializer.validated_data['location'],
            audition_serializer.validated_data['date']
        )
        sender = instance._request_user
        recipient = instance.user
        message = pm_write(
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body,
            skip_notification=True,
            set_thread=True)

        audition_serializer.save(message_id=message.id)

        # send message notification to sender.
        if recipient.preferences.app_notification:
            send_app_notification(
                sender=sender,
                verb=u"sent a message ",
                action_object=message,
                target=recipient,
                description=u"Sent a message.")
        # send push notification
        extra_data = ({"extra": {"data": json.dumps({"job_id": instance.job.id})}})
        send_push_notification(recipient, JOB_INVITE_MESSAGE, **extra_data)
        if recipient.preferences.email_notification:
            context = {"first_name": instance.user.first_name,
                       "job": instance.job,
                       "url": django_settings.JOB_OPPORTUNITIES_URL,
                       "domain": django_settings.DOMAIN}
            JobInviteEmailNotification(recipient.email, context=context).send()

    if instance.state == State.REJECTED:
        data = instance._extra_data
        Application.objects.filter(id=instance.id).update(
            reason_for_rejection=data.get('reason_for_rejection'))
        extra_data = ({"extra": {"data": json.dumps({"job_id": instance.job.id})}})
        send_push_notification(instance.user, "Your Application on audition {} has been rejected.".format(instance.job.title), **extra_data)
