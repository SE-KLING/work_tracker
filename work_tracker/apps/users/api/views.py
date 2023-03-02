from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.throttling import UserRateThrottle

from .serializers import RegistrationSerializer

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
