@echo off

if "%1"=="" (
    echo Использование: make ^<command^>
    echo.
    echo Команды:
    echo   install      - Установить зависимости
    echo   run         - Запустить сервер
    echo   migrate     - Применить миграции
    echo   test        - Запустить тесты
    echo   lint        - Проверить код
    echo   format      - Форматировать код
    echo   docker-up   - Запустить Docker
    echo   docker-down - Остановить Docker
    goto :eof
)

if "%1"=="install" (
    poetry install --no-interaction
    goto :eof
)

if "%1"=="run" (
    poetry run python manage.py runserver
    goto :eof
)

if "%1"=="migrate" (
    poetry run python manage.py migrate
    goto :eof
)

if "%1"=="test" (
    poetry run pytest -v
    goto :eof
)

if "%1"=="lint" (
    poetry run black --check .
    poetry run isort --check-only .
    poetry run flake8 .
    goto :eof
)

if "%1"=="format" (
    poetry run black .
    poetry run isort .
    goto :eof
)

if "%1"=="docker-up" (
    docker-compose up -d
    goto :eof
)

if "%1"=="docker-down" (
    docker-compose down
    goto :eof
)

echo Неизвестная команда: %1
