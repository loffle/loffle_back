from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperuserOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        return bool(request.user and request.user.is_superuser)
