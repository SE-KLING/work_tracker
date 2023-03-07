from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from work_tracker.apps.users.forms import UserAdminChangeForm, UserAdminCreateForm
from work_tracker.apps.users.models import User


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreateForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "rate")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password1", "password2")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "rate")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    list_display = (
        "email",
        "name",
        "rate",
        "created_at",
        "is_active",
        "deactivated_at",
        "is_superuser",
    )
    list_filter = ("is_active", "is_superuser")
    ordering = ("email",)
    search_fields = ["name", "email"]

    def delete_model(self, request, obj):
        obj.deactivated_at = timezone.now()
        obj.is_active = False
        obj.save()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)
