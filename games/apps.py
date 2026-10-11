"""Конфигурация Django-приложения games."""

from django.apps import AppConfig


class GamesConfig(AppConfig):
    """Приложение игр библиотеки."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "games"
