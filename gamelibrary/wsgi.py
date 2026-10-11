"""Точка входа WSGI-сервера для проекта gamelibrary.

Модуль предоставляет объект application, через который WSGI-сервер
передаёт HTTP-запросы в Django-приложение.

Подробнее: https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamelibrary.settings')

application = get_wsgi_application()
