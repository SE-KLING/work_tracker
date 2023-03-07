from django import forms
from django.contrib.auth import forms as admin_forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from work_tracker.apps.users.models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        fields = "__all__"
        field_classes = {"email": forms.EmailField}

    def save(self, commit=True):
        cd = self.cleaned_data
        user = super().save(commit=False)
        # Update deactivated_at field to reflect active status
        if cd["is_active"] and user.deactivated_at:
            user.deactivated_at = None

        # Update deactivated_at field to reflect inactive status
        if not cd["is_active"] and not user.deactivated_at:
            user.deactivated_at = timezone.now()

        user.save()
        return user


class UserAdminCreateForm(admin_forms.UserCreationForm):
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    rate = forms.DecimalField(
        label=_("Hourly Rate (€)"), min_value=0, decimal_places=2, required=False
    )

    def clean(self):
        cd = self.cleaned_data
        rate_required_conditions = [
            not cd["is_superuser"],
            not cd["is_staff"],
            not cd["rate"],
        ]
        # Raise validation errors for "employees" with no entered hourly rate.
        if all(rate_required_conditions):
            raise forms.ValidationError(
                {"rate": "Non-staff/Non-super users must enter their hourly rate."}
            )

    def save(self, commit=True):
        cd = self.cleaned_data
        user = super().save(commit=False)
        # Manually set user's full name.
        name = " ".join(map(str, [cd["first_name"], cd["last_name"]])).strip()
        user.name = name
        user.save()
        return user

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "rate", "password1", "password2")
        field_classes = {"email": forms.EmailField}

        error_messages = {
            "email": {"unique": _("This email address has already been used.")}
        }
