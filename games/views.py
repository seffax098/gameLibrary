"""View-функции приложения games."""

from django.http import HttpResponse


def games(request):
    """Список игр библиотеки."""
    return HttpResponse("Список игр")


def game_detail(request, game_id):
    """Карточка игры."""
    return HttpResponse(f"Игра {game_id}")
