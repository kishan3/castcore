"""Custom permissions for stageroute jobs."""
from rest_framework import permissions
from project.models import Job


class IsJobOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user != Job.objects.get(id=view.kwargs.get("job_id")).created_by:
            return False
        return True
