"""
This module provides an API to the django-postman application.

for an easy usage from other applications in the project.

Sample:
Suppose an application managing Event objects. Whenever a new Event is generated,
you want to broadcast an announcement to Users who have subscribed
to be informed of the availability of such a kind of Event.

from postman.api import pm_broadcast
events = Event.objects.filter(...)
for e in events:
    pm_broadcast(
        sender=e.author,
        recipients=e.subscribers,
        subject='New {0} at Our School: {1}'.format(e.type, e.title),
        body=e.description)
"""
from __future__ import unicode_literals
import json

from django.db.models import Q

from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model

from django.utils.timezone import now

from rest_framework import mixins, viewsets
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated

from postman.models import Message, STATUS_PENDING, STATUS_ACCEPTED
from actstream import action
from messaging.tasks import send_push_notification
from messaging.messages import POSTMAN_REPLY_MESSAGE

from .models import get_order_by


def _get_site():
    # do not require the sites framework to be installed ; and no request object is available here
    return Site.objects.get_current() if Site._meta.installed else None


def pm_broadcast(sender, recipients, subject, body="", skip_notification=False):
    """
    Broadcast a message to multiple Users.

    For an easier cleanup, all these messages are directly marked as archived
    and deleted on the sender side.
    The message is expected to be issued from a trusted application, so moderation
    is not necessary and the status is automatically set to 'accepted'.

    Optional argument:
        ``skip_notification``: if the normal notification event is not wished
    """
    message = Message(
        subject=subject,
        body=body,
        sender=sender,
        sender_archived=True,
        sender_deleted_at=now(),
        moderation_status=STATUS_ACCEPTED,
        moderation_date=now(),
    )
    if not isinstance(recipients, (tuple, list)):
        recipients = (recipients,)
    for recipient in recipients:
        message.recipient = recipient
        message.pk = None
        message.save()
        if not skip_notification:
            message.notify_users(STATUS_PENDING, _get_site())


def pm_write(
    sender,
    recipient,
    subject=None,
    body="",
    skip_notification=False,
    auto_archive=False,
    auto_delete=False,
    auto_moderators=None,
    set_thread=False,
):
    """
    Write a message to a User.

    Contrary to pm_broadcast(), the message is archived and/or deleted on
    the sender side only if requested.
    The message may come from an untrusted application, a gateway for example,
    so it may be useful to involve some auto moderators in the processing.

    Optional arguments:
        ``skip_notification``: if the normal notification event is not wished
        ``auto_archive``: to mark the message as archived on the sender side
        ``auto_delete``: to mark the message as deleted on the sender side
        ``auto_moderators``: a list of auto-moderation functions
    """
    if subject is None or subject == "":
        raise ValidationError("Subject can not be blank")
    message = Message(subject=subject, body=body, sender=sender, recipient=recipient)
    initial_status = message.moderation_status
    if auto_moderators:
        message.auto_moderate(auto_moderators)
    else:
        message.moderation_status = STATUS_ACCEPTED
    message.clean_moderation(initial_status)
    if auto_archive:
        message.sender_archived = True
    if auto_delete:
        message.sender_deleted_at = now()
    message.save()
    if set_thread:
        message.thread = message
    message.save()
    if not skip_notification:
        action.send(
            recipient, verb="got a new message.", description="Got the message."
        )
        # message.notify_users(initial_status, _get_site())
    return message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.first_name")
    recipient_name = serializers.CharField(source="recipient.first_name")

    class Meta:
        model = Message


class InboxAPIView(mixins.ListModelMixin, viewsets.GenericViewSet):

    folder_name = "inbox"
    serializer_class = MessageSerializer

    def list(self, request, *args, **kwargs):
        params = {}
        option = kwargs.get("option")
        if option:
            params["option"] = option
        order_by = get_order_by(self.request.GET)
        if order_by:
            params["order_by"] = order_by
        queryset = getattr(Message.objects, self.folder_name)(
            self.request.user, **params
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class WriteAPIView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        recipient = request.data.get("recipient")
        if not recipient:
            raise ValidationError("Please provide one recipient.")
        else:
            user_model = get_user_model()
            try:
                user = user_model.objects.get(Q(email=recipient) | Q(phone=recipient))
            except user_model.DoesNotExist:
                raise NotFound("user not found.")

        sender = request.user
        recipient = user
        subject = request.data.get("subject")
        body = request.data.get("body")
        write = pm_write(sender, recipient, subject, body)
        # send push notification
        # extra_data = ({"extra": {"data": str({"message_id": write.id})}})
        # send_push_notification(recipient, POSTMAN_MESSAGE, **extra_data)
        m_ser = MessageSerializer(write)
        return Response(m_ser.data)


class ReplyAPIView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        message_id = kwargs.get("message_id")
        try:
            parent_message = Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            raise NotFound("Message with id {} does not exists.".format(message_id))
        if request.user.id not in [
            parent_message.sender.id,
            parent_message.recipient.id,
        ]:
            raise ValidationError(
                "You can not message to this message id {}.".format(message_id)
            )
        if (
            parent_message and not parent_message.thread_id
        ):  # at the very first reply, make it a conversation
            parent_message.thread = parent_message
            parent_message.save()

        body = request.data.get("body")
        reply = pm_write(
            sender=request.user,
            recipient=parent_message.sender,
            subject=parent_message.subject,
            body=body,
            skip_notification=True,
        )

        if parent_message:
            reply.parent = parent_message
            reply.thread_id = parent_message.thread_id
        reply.save()
        # send reply notification to sender.
        action.send(
            parent_message.sender,
            verb="got a reply ",
            action_object=reply,
            target=parent_message,
            description="Got the reply.",
        )
        # send push notification
        extra_data = {
            "extra": {
                "data": json.dumps(
                    {"message": {"message_id": reply.id, "thread_id": reply.thread_id}}
                )
            }
        }
        send_push_notification(
            parent_message.sender,
            POSTMAN_REPLY_MESSAGE.format(**{"username": request.user.first_name}),
            **extra_data
        )

        r_ser = MessageSerializer(reply)
        return Response(r_ser.data)


class ConversationAPIView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        thread_id = kwargs.get("thread_id")
        self.filter = Q(thread=thread_id)
        queryset = Message.objects.thread(request.user, self.filter)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
