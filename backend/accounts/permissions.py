"""
Custom permission classes for the customization system.
"""
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: only the owner can modify,
    everyone can read.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # Write permissions only for the owner
        return hasattr(obj, "user") and obj.user == request.user


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: only the owner or admin can access.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return hasattr(obj, "user") and obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """
    Admin can do anything, others can only read.
    """
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user and request.user.is_staff
