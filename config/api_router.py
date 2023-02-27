from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from work_tracker.apps.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("api", UserViewSet)


app_name = "api"
urlpatterns = router.urls
