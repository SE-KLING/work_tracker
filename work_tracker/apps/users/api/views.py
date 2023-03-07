from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import ChangePasswordSerializer, RegistrationSerializer

User = get_user_model()


class RegistrationThrottle(UserRateThrottle):
    rate = "5/hour"
    scope = "registration"


class RegisterView(CreateAPIView):
    """
    Initial Registration view that allows for User creation.
    """

    serializer_class = RegistrationSerializer
    throttle_classes = [RegistrationThrottle]
    authentication_classes = []


class PasswordChangeView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        user = self.request.user
        return user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # Check if current password is valid
            current_password = serializer.validated_data.get("current_password", "")
            if not user.check_password(current_password):
                return Response(
                    {"current_password": ["Current password is incorrect."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set new password for User
            new_password = serializer.validated_data.get("new_password", "")
            user.set_password(new_password)
            user.save()

            response = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Your password has successfully been updated.",
                "data": {},
            }
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
