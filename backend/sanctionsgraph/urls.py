"""URL configuration for the sanctionsgraph project."""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from screening.views import AgentViewSet, MatchViewSet, ScreenView, ScreeningCaseViewSet

router = DefaultRouter()
router.register(r"agents", AgentViewSet, basename="agent")
router.register(r"cases", ScreeningCaseViewSet, basename="case")
router.register(r"matches", MatchViewSet, basename="match")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/screen/", ScreenView.as_view(), name="screen"),
    path("api/", include(router.urls)),
]
