from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class PasswordValidator:
    """
    Validator which validates that an entered password:

    - Is not equivalent to the requesting User's email address.
    - Contains the minimum required characters specified
    - Is not purely numeric.
    """

    def __init__(self, email: str = None, min_length: int = 8):
        self.email = None
        self.min_length = min_length

    def set_context(self, field):
        self.email = field.parent.initial_data.get("email", field.context["request"].user.email).lower()

    def __call__(self, value):
        # Assert that password is not equal to requesting User's email address.
        if value.lower() == self.email:
            raise ValidationError("Your password may not be the same as your email.")
        # Assert that password contains minimum required characters.
        elif len(value) < self.min_length:
            raise ValidationError(
                f"Your password is too short. It must contain at least "
                f"{self.min_length} characters."
            )
        # Assert that password is not purely numeric.
        elif value.isdigit():
            raise ValidationError("Your password may not be entirely numeric.")


class PasswordField(serializers.CharField):
    """
    Custom password field that is validated using the PasswordValidator() class.
    """

    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        kwargs["validators"] = [PasswordValidator()]
        super().__init__(**kwargs)


class EnumField(serializers.ChoiceField):
    """
    Custom Enum Serializer field to be used with the 'django-enumfields' library to easily serialize and display enum
    choices and selections.
    """
    NAME_FIELDS = {"name", "label"}
    VALUE_FIELDS = {"name", "value"}
    ALL_FIELDS = NAME_FIELDS.union(VALUE_FIELDS)

    def __init__(self, enum, name_field: str = "label", value_field: str = "name", fields=None, choices=None, **kwargs):
        if name_field not in self.NAME_FIELDS:
            raise ValueError(f'Invalid "name_field" arg: {name_field}')
        if value_field not in self.VALUE_FIELDS:
            raise ValueError(f'Invalid "value_field" arg: {value_field}')
        if fields:
            if not set(fields).issubset(self.ALL_FIELDS):
                raise ValueError(f"Invalid fields arg. Valid values: {self.ALL_FIELDS}")
        self.enum = enum
        self.name_field = name_field
        self.value_field = value_field
        self.fields = fields
        if choices is None:
            choices = list(enum)
        try:
            unique_choices = {e if isinstance(e, enum) else enum(e) for e in choices}
        except ValueError:
            raise ValueError("Choices should be an iterable of enum members or values.")
        else:
            self.enum_choices = sorted(unique_choices, key=list(enum).index)
        # choices used in forms/meta:
        kwargs["choices"] = [
            (getattr(e, value_field), getattr(e, name_field)) for e in self.enum_choices
        ]
        super().__init__(**kwargs)

    def to_representation(self, enum):
        if not enum:
            return None
        if self.fields:
            return {k: getattr(enum, k) for k in self.fields}
        else:
            return getattr(enum, self.value_field)

    def to_internal_value(self, input_data):
        if input_data == "" and self.allow_blank:
            return None
        if isinstance(input_data, self.enum):
            return input_data
        try:
            if self.value_field == "value":
                # Get enum with: Enum(value)
                return self.enum(self.choice_strings_to_values[str(input_data)])
            else:
                # Get enum by searching for "value_field"
                # Only required when using "name" for "value_field"
                return next(
                    e for e in self.enum_choices
                    if getattr(e, self.value_field) == input_data
                )
        except (AttributeError, KeyError, ValueError, StopIteration):
            self.fail("invalid_choice", input=input_data)
