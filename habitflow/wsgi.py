import os
from dotenv import load_dotenv

from django.core.wsgi import get_wsgi_application

# Загружаем переменные окружения
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'habitflow.settings')

application = get_wsgi_application()