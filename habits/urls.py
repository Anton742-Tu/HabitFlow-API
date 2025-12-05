from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HabitCompletionViewSet, HabitViewSet

router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"completions", HabitCompletionViewSet, basename="completion")

urlpatterns = [
    path("", include(router.urls)),
]
