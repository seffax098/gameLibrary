"""Корневая маршрутизация проекта gamelibrary."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("games/", include("games.urls")),
    path("sessions/", include("gamesessions.urls")),
]

if settings.DEBUG_TOOLBAR_ENABLED:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
    )

handler404 = "homepage.views.page_not_found"  # pylint: disable=invalid-name
