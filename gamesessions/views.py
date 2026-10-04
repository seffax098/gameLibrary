"""View-функции приложения gamesessions."""

from django.http import HttpResponse


def sessions(request):
    """Список игровых сессий."""
    return HttpResponse("Список игровых сессий")


def session_detail(request, session_id):
    """Карточка игровой сессии."""
    return HttpResponse(f"Сессия {session_id}")
