.PHONY: format lint check test migrate run

format:
	black .
	isort .

lint:
	flake8 .

type-check:
	mypy .

check: lint type-check

test:
	python manage.py test

migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python manage.py runserver

quality: format check