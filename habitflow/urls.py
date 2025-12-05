from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views import View
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


# Класс для корневой страницы прямо в urls.py
class APIRootView(View):
    def get(self, request):
        return JsonResponse(
            {
                "message": "Добро пожаловать в HabitFlow API!",
                "version": "1.0.0",
                "endpoints": {
                    "api_docs": "/swagger/",
                    "api_docs_redoc": "/redoc/",
                    "habits": "/api/habits/",
                    "completions": "/api/completions/",
                    "token": "/api/token/",
                    "token_refresh": "/api/token/refresh/",
                    "admin": "/admin/",
                },
                "authentication": "JWT Token based",
                "pagination": "5 items per page for habits",
            }
        )


# Настройка Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="HabitFlow API",
        default_version="v1",
        description="API для трекера полезных привычек",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@habitflow.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", APIRootView.as_view(), name="api-root"),
    path("admin/", admin.site.urls),
    # API документация
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # API
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("habits.urls")),
]
