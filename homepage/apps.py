"""Конфигурация Django-приложения homepage."""

from django.apps import AppConfig


class HomepageConfig(AppConfig):
    """Приложение главной страницы."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "homepage"
