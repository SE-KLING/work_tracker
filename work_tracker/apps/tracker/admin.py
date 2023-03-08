from django.contrib import admin
from django.template.defaultfilters import truncatechars

from work_tracker.apps.tracker import models
from work_tracker.apps.tracker.forms import EntryAdditionForm


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "name", "short_description")
    search_fields = ("name",)
    ordering = ("name",)
    fieldsets = ((None, {"fields": ("name", "description")}),)

    @staticmethod
    def short_description(obj: models.Company) -> str:
        """
        Return the company's description in a truncated form, to allow for better displaying in the admin site.

        Returns:
            str: Truncated Company description.
        """
        return truncatechars(obj.description, 150)


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "project_users", "company", "name")
    search_fields = ("name",)
    ordering = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("users")

    @staticmethod
    def project_users(obj: models.Project) -> str:
        """
        Return a truncated list of users involved in project as a string value to display in Project admin list.

        Returns:
            str: List of users involved in current Project.
        """
        return ", ".join([str(p) for p in obj.users.all()][:6])


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "user", "code", "name", "project", "type", "status", "short_description")
    search_fields = ("name", "user", "code")
    ordering = ("status",)

    @staticmethod
    def short_description(obj: models.Task) -> str:
        """
        Return the Task's description in a truncated form, to allow for better displaying in the admin site.

        Returns:
            str: Truncated Task description.
        """
        return truncatechars(obj.description, 100)


@admin.register(models.Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "entry_user", "task", "hours", "bill", "comment")
    ordering = ("status",)
    form = EntryAdditionForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("task")

    @staticmethod
    def entry_user(obj: models.Entry) -> str:
        """
        Return the email address of the user the current Entry is associated with.

        Returns:
            str: Email address of Entry user.
        """
        return obj.task.user.email
