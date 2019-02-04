"""Serializers for application app."""
from rest_framework import serializers

from .models import Application, MobileAppVersion, AuditionInvite
from project.serializers import JobShortSerializer


class AuditionInviteSerializer(serializers.ModelSerializer):
    """Audition details serializer."""
    message_id = serializers.IntegerField(required=False)

    class Meta:
        """Meta."""

        model = AuditionInvite
        fields = ('title', 'description', 'location', 'date',
                  'message_id', 'applications')
        extra_kwargs = {'date': {'required': True},
                        'title': {'required': True},
                        'description': {'required': True},
                        'location': {'required': True}}


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for application model."""

    exclude_user_fields = ['phone', 'email']
    audition_invites = AuditionInviteSerializer(many=True)
    user = serializers.SerializerMethodField()

    class Meta:
        """Meta class."""

        model = Application
        fields = ('id', 'updated_at', 'state', 'user', 'job',
                  'audition_invites', 'reason_for_rejection',)

    def get_user(self, obj):
        # Imported here to avoid circular import error.
        from users.serializers import UserSerializer
        extra_kwargs = {
            'exclude_fields': self.exclude_user_fields
        }
        serializer = UserSerializer(obj.user, context={'request': self.context['request']}, **extra_kwargs)
        return serializer.data


class ApplicationDetailSerializer(ApplicationSerializer):
    job = JobShortSerializer()

    class Meta:
        model = Application


class MobileAppVersionSerializer(serializers.ModelSerializer):
    """Mobile version serializer."""

    class Meta:
        """Meta."""

        model = MobileAppVersion
        fields = ('version_code', 'is_required', 'url', 'message', 'app_type')
