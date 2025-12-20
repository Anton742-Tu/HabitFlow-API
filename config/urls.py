from django.conf import settings
from django.contrib import admin
from django.urls import include, path

# from django.views.generic import RedirectView

# from drf_yasg import openapi
# from drf_yasg.views import get_schema_view
# from rest_framework import permissions

# from docs.views import APIDocumentationView, api_spec_json

# Настройка Swagger документации
# schema_view = get_schema_view(
#    openapi.Info(
#        title="HabitFlow API",
#        default_version="v1",
#        description="""
#        <h2>📚 Документация API для трекера привычек HabitFlow</h2>

#        <h3>📖 О проекте</h3>
#        <p>API для трекинга привычек по методологии <strong>Atomic Habits</strong> (Джеймс Клир).</p>

#        <h3>🔐 Аутентификация</h3>
#        <p>Используется JWT аутентификация. Получите токен через эндпоинт <code>/api/users/token/</code></p>

#        <h3>📋 Основные возможности:</h3>
#        <ul>
#            <li>✅ Создание и управление привычками</li>
#            <li>✅ Отслеживание выполнения</li>
#            <li>✅ Валидация по правилам Atomic Habits</li>
#            <li>✅ Telegram интеграция для напоминаний</li>
#            <li>✅ Статистика и аналитика</li>
#        </ul>

#        <h3>🚀 Быстрый старт:</h3>
#        <ol>
#            <li>Зарегистрируйтесь через <code>/api/users/register/</code></li>
#            <li>Получите JWT токен через <code>/api/users/token/</code></li>
#            <li>Используйте токен в заголовке: <code>Authorization: Bearer {token}</code></li>
#        </ol>

#        <hr>
#        <p><strong>📱 Telegram бот:</strong> @anton_tumashov_bot</p>
#        <p><strong>📧 Поддержка:</strong> Для вопросов обращайтесь к разработчикам</p>
#        """,
#        terms_of_service="https://habitflow.ru/terms/",
#        contact=openapi.Contact(email="support@habitflow.ru"),
#        license=openapi.License(name="MIT License"),
#    ),
#    public=True,
#    permission_classes=(permissions.AllowAny,),
# )

urlpatterns = [
    # Админка Django
    path("admin/", admin.site.urls),
    # API документация
    # path("", RedirectView.as_view(url="/swagger/", permanent=False)),
    # path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    # path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # path("openapi.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    # API endpoints
    path("api/", include("users.urls")),
    path("api/", include("habits.urls")),
    path("telegram/", include("telegram_bot.urls")),
    # Дополнительная документация
    # path("docs/", APIDocumentationView.as_view(), name="api-docs"),
    # path("docs/spec.json", api_spec_json, name="api-spec-json"),
]

# Для дебага включаем статику
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
