"""Notification views."""
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from push_notifications.api.rest_framework import GCMDeviceSerializer, DeviceViewSetMixin
from push_notifications.models import GCMDevice


class GCMDeviceViewSet(DeviceViewSetMixin, viewsets.ModelViewSet):
    """Overriding permission to allow any."""

    queryset = GCMDevice.objects.all()
    serializer_class = GCMDeviceSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        gcm = self.request.user.gcmdevice_set.last()
        if gcm:
            serializer = self.get_serializer(gcm, data=self.request.data, partial=True)
            serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response(serializer.data)
