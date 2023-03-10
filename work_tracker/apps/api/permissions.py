from rest_framework.permissions import BasePermission


class IsAuthorisedUser(BasePermission):
    """
    Permission allowing only staff or superusers to create, update and delete objects.
    """
    message = 'Only staff users may access this functionality.'
    PROTECTED_METHODS = ('POST', 'PATCH', 'PUT', 'DELETE')

    def has_permission(self, request, view):
        if request.method in self.PROTECTED_METHODS:
            return bool(request.user.is_staff or request.user.is_superuser)
        return True


class ProjectSpecificTasks(BasePermission):
    """
    Permission allowing only users associated with the current Task's project to access its detail view, displaying
    Entries.
    """
    message = 'You cannot access Task details for tasks not assigned to you.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        has_permission = any([user.is_staff, user.is_superuser]) or obj.project in request.user.projects.all()
        return has_permission


class UserSpecificEntries(BasePermission):
    """
    Permission allowing only users associated with the current Entry's task to access the detail views.
    """
    message = 'You cannot access Entries for tasks not assigned to you.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        has_permission = any([user.is_staff, user.is_superuser]) or obj.task in request.user.entries.all()
        return has_permission
