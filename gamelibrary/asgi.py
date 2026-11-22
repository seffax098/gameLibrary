"""Точка входа ASGI-сервера для проекта gamelibrary.

Модуль предоставляет объект application, через который ASGI-сервер
передаёт HTTP-запросы в Django-приложение.

Подробнее: https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamelibrary.settings')

application = get_asgi_application()
