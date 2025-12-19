.PHONY: up down build logs shell web-shell db-shell restart clean test migrate

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-db:
	docker-compose logs -f db

logs-redis:
	docker-compose logs -f redis

logs-celery:
	docker-compose logs -f celery_worker

logs-bot:
	docker-compose logs -f telegram_bot

shell:
	docker-compose exec web bash

web-shell:
	docker-compose exec web python manage.py shell

db-shell:
	docker-compose exec db psql -U postgres -d habitflow_db

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -f

test:
	docker-compose exec web python manage.py test

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

status:
	docker-compose ps
	docker-compose images

# Запуск в production режиме
prod-up:
	DOCKER_TARGET=production SERVER_COMMAND="gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3" docker-compose up -d

# Запуск без некоторых сервисов
minimal-up:
	docker-compose up -d db redis web
