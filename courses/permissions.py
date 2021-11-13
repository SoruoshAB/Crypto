from datetime import datetime, timedelta

from django.utils.translation import ugettext as _
from rest_framework import permissions
from rest_framework.permissions import BasePermission

from courses.models.order import Order


class SuperUserPermission(BasePermission):
    """
    Global permission Super user
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Instance must have an attribute named `owner`.
        return obj.user == request.user


class IsOwnerLesson(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Instance must have an attribute named `owner`.
        print("request ", request.META)
        return request.user in list(obj.chapter.course.user.all())


def check_perm_owner_update(request, instance):
    if request.user.is_superuser:
        return True
    if isinstance(instance, Order) and instance.user == request.user:
        return True
    else:
        return False
