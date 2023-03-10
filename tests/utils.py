from rest_framework_simplejwt.tokens import RefreshToken

from work_tracker.apps.users.models import User


class JWTMixin:
    """
    Custom Mixin to allow for easier JWT-authenticated requests in tests.
    """

    # noinspection PyMethodMayBeStatic
    def get_token(self, user: User):
        """
        Return valid JWT access token for requesting user to be used in request authentication.
        """
        refresh_token = RefreshToken.for_user(user)
        return refresh_token.access_token

    # noinspection PyMethodMayBeStatic
    def get_client(self, user: User):
        """
        Return existing client used by TestCase class, with additional Auth headers to allow for authenticated calls.
        """
        client = self.client_class()
        token = self.get_token(user)
        client.credentials(**{'HTTP_AUTHORIZATION': f'Bearer {token}'})
        return client
