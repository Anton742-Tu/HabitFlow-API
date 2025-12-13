"""
Скрипт для создания .env файла из шаблона .env.example
"""

import sys
from pathlib import Path


def setup_env():
    """Создает .env файл если он не существует"""
    env_example = Path(".env.example")
    env_file = Path(".env")

    if not env_example.exists():
        print("❌ Файл .env.example не найден!")
        sys.exit(1)

    if env_file.exists():
        print("⚠️  Файл .env уже существует. Переименовываю в .env.backup")
        env_file.rename(".env.backup")

    # Читаем шаблон
    with open(env_example, "r", encoding="utf-8") as f:
        content = f.read()

    # Заменяем значения по умолчанию
    import secrets

    secret_key = secrets.token_urlsafe(50)
    content = content.replace("your-secret-key-here-change-in-production", secret_key)

    # Записываем новый .env файл
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Создан новый файл .env")
    print(f"✅ Сгенерирован SECRET_KEY: {secret_key[:20]}...")
    print("\n⚠️  Не забудьте настроить другие переменные в .env файле!")
    print("📄 Отредактируйте файл .env и настройте:")
    print("   - Пароль PostgreSQL (POSTGRES_PASSWORD)")
    print("   - Настройки базы данных")
    print("   - Другие параметры по необходимости")


if __name__ == "__main__":
    setup_env()
