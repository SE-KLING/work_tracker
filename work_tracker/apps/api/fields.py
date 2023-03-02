from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class PasswordValidator:
    """
    Verify that a user does not attempt to set a password which matches their email address
    """

    def __init__(self, min_length: str = 8):
        self.email = None
        self.min_length = min_length

    def set_context(self, field):
        self.email = field.parent.initial_data.get(
            "email", field.context["request"].user.email
        ).lower()

    def __call__(self, value):
        if value.lower() == self.email:
            raise ValidationError("Your password may not be the same as your email.")
        elif len(value) < self.min_length:
            raise ValidationError(
                f"Your password is too short. It must contain at least "
                f"{self.min_length} characters."
            )
        elif value.isdigit():
            raise ValidationError("Your password may not be entirely numeric.")


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        kwargs["validators"] = [PasswordValidator()]
        super().__init__(**kwargs)
