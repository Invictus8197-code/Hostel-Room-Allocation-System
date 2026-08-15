from rest_framework import permissions
from backend.apps.accounts.models import User

class IsAdminOrWarden(permissions.BasePermission):
    """
    Allows access only to users with role ADMIN or WARDEN.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.Role.ADMIN, User.Role.WARDEN]
        )

class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to users with role ADMIN.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.ADMIN
        )
