from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from work_tracker.apps.users.api.views import RegisterView

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

# router.register("user/register/", RegisterView)


app_name = "api"
urlpatterns = [
    # API AUTH TOKENS
    path("user/auth-token/", TokenObtainPairView.as_view(), name="auth-token"),
    path(
        "user/auth-token/refresh/",
        TokenRefreshView.as_view(),
        name="auth-token-refresh",
    ),
    path(
        "user/auth-token/verify/", TokenVerifyView.as_view(), name="auth-token-refresh"
    ),
    path("user/register/", RegisterView.as_view(), name="user-register"),
    path("", include(router.urls)),
]
