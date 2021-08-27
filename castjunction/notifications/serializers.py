# -*- coding: utf-8 -*-

from rest_framework import serializers

from .models import Action


class ActionSerializer(serializers.ModelSerializer):
    actor_model_name = serializers.SerializerMethodField()
    target_model_name = serializers.SerializerMethodField()
    action_model_name = serializers.SerializerMethodField()
    actor_name = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")

    class Meta:
        model = Action
        exclude = (
            "actor_content_type",
            "target_content_type",
        )

    def get_actor_model_name(self, obj):
        return obj.actor_content_type.name

    def get_target_model_name(self, obj):
        if obj.target_object_id:
            return obj.target_content_type.name
        return None

    def get_action_model_name(self, obj):
        if obj.action_object:
            return obj.action_object_content_type.name
        return None

    def get_actor_name(self, obj):
        if obj.actor.first_name:
            actor_name = obj.actor.first_name
        elif obj.actor.email:
            actor_name = obj.actor.email.split("@")[0]
        else:
            actor_name = "User"
        return actor_name

    def update(self, instance, validated_data):
        """
        To mark notification as read:
        - Endpoint: {base_url}/notifications/{notification_id}/
        - Request: PATCH
        - unread: False
        """
        allowed_fields = ["public", "unread", "data"]
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        instance.save()
        return instance
