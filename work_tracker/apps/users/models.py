from functools import partial
from uuid import uuid4

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

AmountField = partial(models.DecimalField, max_digits=8, decimal_places=2)


class TimeStampedModel(models.Model):
    """
    Abstract model which auto-tracks when Model instances are created and updated.
    """
    created_at = AutoCreatedField()
    modified_at = AutoLastModifiedField()

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, email, password):
        if email is None:
            raise TypeError("Users must have an email address.")
        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password):
        if password is None:
            raise TypeError("Superusers must have a password.")
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class AbstractEmailUser(AbstractBaseUser, PermissionsMixin):
    """
    Abstract model enforcing 'email' as User's main username field for authentication.
    """
    email = models.EmailField(_("email address"), max_length=255, unique=True)
    is_staff = models.BooleanField(_("staff status"), default=False,
                                   help_text=_("Designates whether the user can log into this admin site."))
    is_active = models.BooleanField(_("active"), default=True,
                                    help_text=_("Designates whether this user should be treated as active. "
                                                "Deselect this instead of deleting accounts."))

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        abstract = True
        ordering = ("email", )


class User(AbstractEmailUser, TimeStampedModel):
    """
    Custom User model allowing for greater customisation whilst still allowing for Django's built-in User functionality.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    deactivated_at = models.DateTimeField(blank=True, null=True)
    rate = AmountField(verbose_name="Hourly Rate", blank=True, null=True, db_index=True)

    objects = UserManager()

    REQUIRED_FIELDS = []

    def save(self, **kwargs):
        self.name = " ".join(map(str, [self.first_name, self.last_name])).strip()
        return super().save(**kwargs)

    def get_short_name(self) -> str:
        """
        Return the user's first name, for more colloquial use.

        Returns:
            str: User first name.
        """
        return self.first_name or self.name or self.email

    def get_full_name(self) -> str:
        """
        Return the user's full name, for more formal use.

        Returns:
            str: User full name.
        """
        return self.name or self.email
