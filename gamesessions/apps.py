"""Конфигурация Django-приложения gamesessions."""

from django.apps import AppConfig


class GamesessionsConfig(AppConfig):
    """Приложение игровых сессий."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "gamesessions"
