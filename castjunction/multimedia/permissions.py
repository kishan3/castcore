"""Custom permissions for stageroute multimedia."""
from rest_framework import permissions


class IsMultimediaOwner(permissions.IsAuthenticated):
    """Permission that checks if this object has a foreign key pointing to the.

    authenticated user of this request
    """

    def has_object_permission(self, request, view, obj):
        return obj.content_object.id == request.user.id
