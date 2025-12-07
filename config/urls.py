from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views import View
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


# Класс для корневой страницы
class APIRootView(View):
    def get(self, request):
        return JsonResponse(
            {
                "message": "Добро пожаловать в HabitFlow API!",
                "version": "1.0.0",
                "endpoints": {
                    "users": "/api/users/",
                    "habits": "/api/habits/",
                    "docs": "/swagger/",
                    "admin": "/admin/",
                },
            }
        )


# Настройка Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="HabitFlow API",
        default_version="v1",
        description="API для трекера полезных привычек",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@config.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", APIRootView.as_view(), name="api-root"),
    path("admin/", admin.site.urls),
    # Документация
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # API приложений
    path("api/users/", include("users.urls")),
    path("api/", include("habits.urls")),
    # Телеграмм Bot
    path("telegram/", include("telegram_bot.urls")),
]
