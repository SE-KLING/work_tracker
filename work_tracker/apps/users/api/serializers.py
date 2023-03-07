from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from work_tracker.apps.api.fields import PasswordField

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(max_length=255)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    rate = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    token = serializers.SerializerMethodField()
    password = PasswordField(style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "rate", "token", "password")

    def create(self, validated_data):
        email = User.objects.normalize_email(validated_data["email"])
        # Verify User's email address is unique in system
        try:
            user = User.objects.get(email__iexact=email)
            raise serializers.ValidationError(
                "A User with that email address already exists."
            )
        except User.DoesNotExist:
            pass

        user = super().create(validated_data)
        user.set_password(self.validated_data["password"])
        user.save()
        return user

    @staticmethod
    def get_token(obj) -> str:
        """
        Return JWT access token on successful registration.

        Returns:
            str: JWT Access token.
        """
        if obj:
            if isinstance(obj, User):
                token = RefreshToken.for_user(obj)
                return str(token.access_token)
        return None


class ChangePasswordSerializer(serializers.Serializer):
    current_password = PasswordField(style={"input_type": "password"})
    new_password = PasswordField(style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError("New password matches current password.")
        return attrs
