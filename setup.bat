@echo off
echo ========================================
echo   Настройка HabitFlow API на Windows
echo ========================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен
    echo Установите Python 3.12 с https://python.org
    pause
    exit /b 1
)

:: Проверка Poetry
poetry --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Poetry не установлен
    echo Устанавливаем Poetry...
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    setx PATH "%APPDATA%\Python\Scripts;%PATH%"
    echo ✅ Poetry установлен
)

:: Установка зависимостей
echo.
echo 📦 Устанавливаем зависимости...
poetry install --no-interaction

:: Установка pre-commit
echo.
echo 🔧 Настраиваем pre-commit...
poetry run pre-commit install

:: Создание .env файла
echo.
echo ⚙️  Создаем .env файл...
if not exist .env (
    copy .env.example .env
    echo ✅ .env файл создан из примера
    echo ⚠️  Отредактируйте .env файл своими настройками
) else (
    echo ✅ .env файл уже существует
)

:: Настройка базы данных
echo.
echo 🗄️  Настраиваем базу данных...
poetry run python manage.py migrate

:: Создание суперпользователя
echo.
echo 👑 Создаем суперпользователя...
set /p create_superuser="Создать суперпользователя? (y/N): "
if /i "%create_superuser%"=="y" (
    poetry run python manage.py createsuperuser
)

echo.
echo ========================================
echo ✅ Настройка завершена успешно!
echo.
echo Доступные команды:
echo   make.bat run        - Запустить сервер
echo   make.bat test       - Запустить тесты
echo   make.bat lint       - Проверить код
echo   make.bat docker-up  - Запустить Docker
echo ========================================
pause
