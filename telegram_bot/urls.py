from django.urls import path

from . import views

urlpatterns = [
    path("webhook/telegram/", views.telegram_webhook, name="telegram-webhook"),
]
