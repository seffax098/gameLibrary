"""View-функции приложения homepage."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from stats import library_stats
from storage import load_library


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание библиотеки, сводка и навигация."""
    games, users, sessions = load_library(settings.DATA_DIR)
    context = {
        "stats": library_stats(games, users, sessions),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Обработчик ошибки 404 для всего проекта (handler404)."""
    return render(request, "404.html", status=404)
