"""View-функции приложения homepage."""

from django.http import HttpResponse


def index(request):
    """Главная страница."""
    return HttpResponse("Игровая библиотека - учёт игр и игровых сессий")
