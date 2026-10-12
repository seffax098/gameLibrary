"""Корневая маршрутизация проекта gamelibrary.

Адреса распределяются между приложениями функцией include(): здесь
задаётся префикс адреса, а остальная часть разбирается в urls.py
соответствующего приложения.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("games/", include("games.urls")),
    path("sessions/", include("gamesessions.urls")),
]

handler404 = "homepage.views.page_not_found"  # pylint: disable=invalid-name
