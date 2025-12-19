from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HabitCompletionViewSet, HabitViewSet

router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"completions", HabitCompletionViewSet, basename="completion")

# Дополнительные маршруты для новых actions
habit_extra_urls = [
    path("habits/stats/", HabitViewSet.as_view({"get": "stats"}), name="habit-stats"),
    path(
        "habits/export/", HabitViewSet.as_view({"get": "export"}), name="habit-export"
    ),
    path(
        "habits/bulk_complete/",
        HabitViewSet.as_view({"post": "bulk_complete"}),
        name="bulk-complete",
    ),
    path(
        "habits/bulk_update_public/",
        HabitViewSet.as_view({"patch": "bulk_update_public"}),
        name="bulk-update-public",
    ),
]

urlpatterns = [
    path("", include(router.urls)),
] + habit_extra_urls
