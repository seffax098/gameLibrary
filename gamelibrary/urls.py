"""Корневая маршрутизация проекта gamelibrary."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("games/", include("games.urls")),
    path("sessions/", include("gamesessions.urls")),
]

if settings.DEBUG_TOOLBAR_ENABLED:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]

handler404 = "homepage.views.page_not_found"  # pylint: disable=invalid-name
