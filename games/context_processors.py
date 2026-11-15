"""Общие сведения для пользовательских страниц библиотеки."""

from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject

from .models import Game


def library_context(request: HttpRequest) -> dict[str, object]:
    """Передать название сайта и число игр для общей навигации."""
    return {
        "site_name": "Игровая библиотека",
        # Другие шаблоны, в том числе админка, счётчик не запрашивают.
        "library_games_count": SimpleLazyObject(Game.objects.count),
    }
