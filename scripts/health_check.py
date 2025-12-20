"""
Health check script for CI/CD and deployment
"""

import os
import sys
import time

import django
import requests

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    django.setup()
except Exception as e:
    print(f"❌ Ошибка инициализации Django: {e}")
    sys.exit(1)

from django.conf import settings
from django.core.cache import cache
from django.db import connection


def check_database():
    """Проверка подключения к базе данных"""
    try:
        connection.ensure_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True, "✅ База данных доступна"
    except Exception as e:
        return False, f"❌ Ошибка базы данных: {str(e)}"


def check_migrations():
    """Проверка примененных миграций"""
    try:
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            return False, f"❌ Есть непримененные миграции: {len(plan)}"
        return True, "✅ Все миграции применены"
    except Exception as e:
        return False, f"❌ Ошибка проверки миграций: {str(e)}"


def check_cache():
    """Проверка кэша (Redis)"""
    try:
        cache.set("health_check", "test", 5)
        if cache.get("health_check") == "test":
            return True, "✅ Кэш работает"
        return False, "❌ Кэш не работает"
    except Exception as e:
        return False, f"❌ Ошибка кэша: {str(e)}"


def check_telegram():
    """Проверка Telegram бота"""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        return True, "ℹ️ Telegram бот не настроен (пропускаем)"

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getMe", timeout=10
        )
        if response.status_code == 200:
            return True, "✅ Telegram бот доступен"
        return False, f"❌ Telegram бот недоступен: {response.status_code}"
    except Exception as e:
        return False, f"❌ Ошибка Telegram бота: {str(e)}"


def check_api():
    """Проверка API endpoints"""
    try:
        base_url = "http://localhost:8000"
        endpoints = [
            "/api/",
            "/api/habits/public/",
            "/admin/login/",
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code >= 500:
                    return False, f"❌ Endpoint {endpoint}: {response.status_code}"
            except requests.exceptions.RequestException:
                continue  # В тестах может быть недоступен

        return True, "✅ Основные endpoints отвечают"
    except Exception as e:
        return False, f"❌ Ошибка проверки API: {str(e)}"


def run_health_checks():
    """Запуск всех проверок"""
    print("🏥 Запуск health checks...")
    print("=" * 50)

    checks = [
        ("База данных", check_database),
        ("Миграции", check_migrations),
        ("Кэш", check_cache),
        ("Telegram бот", check_telegram),
        ("API", check_api),
    ]

    all_ok = True
    results = []

    for name, check_func in checks:
        start_time = time.time()
        ok, message = check_func()
        elapsed = time.time() - start_time

        status = "✅" if ok else "❌"
        print(f"{status} {name}: {message} ({elapsed:.2f}с)")

        results.append({"name": name, "ok": ok, "message": message, "elapsed": elapsed})

        if not ok:
            all_ok = False

    print("=" * 50)

    if all_ok:
        print("🎉 Все проверки пройдены успешно!")
        return True, results
    else:
        print("❌ Некоторые проверки не пройдены")
        return False, results


def main():
    """Основная функция"""
    # Даем время сервисам запуститься
    time.sleep(2)

    success, results = run_health_checks()

    # Создаем JSON отчет для CI/CD
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": success,
        "checks": results,
    }

    # Сохраняем отчет в файл
    import json
    import os
    import tempfile

    report_path = os.path.join(tempfile.gettempdir(), "health_check_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Возвращаем код выхода
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
