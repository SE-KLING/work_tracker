from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from work_tracker.apps.api.components.tracker.views import CompanyViewSet, EntryViewSet, ProjectViewSet, TaskViewSet
from work_tracker.apps.api.components.users.views import PasswordChangeView, RegisterView

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("entry", EntryViewSet, basename="entry")
router.register("company", CompanyViewSet, basename="company")
router.register("project", ProjectViewSet, basename="project")
router.register("task", TaskViewSet, basename="task")

app_name = "api"
urlpatterns = [
    # USER AUTH ENDPOINTS
    path("user/auth-token/", TokenObtainPairView.as_view(), name="auth-token"),
    path("user/auth-token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("user/auth-token/verify/", TokenVerifyView.as_view(), name="auth-token-verify"),

    # USER ENDPOINTS
    path("user/register/", RegisterView.as_view(), name="user-register"),
    path("user/update-password/", PasswordChangeView.as_view(), name="password-change"),
    path("", include(router.urls)),
]
