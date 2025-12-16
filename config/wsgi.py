import os

from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
