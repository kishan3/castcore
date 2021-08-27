"""Custom permissions for stageroute users."""
from rest_framework import permissions
from .models import User, PersonType


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        """Check for object level permissions."""
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsCastingDirector(permissions.BasePermission):
    """Check permission of user if he/she is casting director or not."""

    def has_permission(self, request, view):
        """Check for permissions."""
        if request.user.user_type == User.PERSON:
            if request.user.person.typ.filter(person_type=PersonType.CASTING_DIRECTOR):
                return True
        return False


class IsSupportGroupMember(permissions.BasePermission):
    """Check if user is from support group or not."""

    def has_permission(self, request, view):
        """Check for permissions."""
        if request.user.groups.filter(name="Support").exists():
            return True
        return False
