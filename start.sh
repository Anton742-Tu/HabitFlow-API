#!/bin/bash
# start.sh

# Ждем базу данных
python /scripts/wait_for_db.py

# Применяем миграции
python manage.py migrate

# Создаем суперпользователя (если нужно)
python /scripts/create_superuser.py

# Запускаем Gunicorn в фоне
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers=3 &

# Запускаем Nginx на переднем плане
nginx -g 'daemon off;'
