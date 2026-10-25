"""View-функции приложения games."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.games import find_game_by_id
from models.sessions import active_sessions, game_progress, hours_played
from storage import load_library


def games(request: HttpRequest) -> HttpResponse:
    """Страница /games/: список игр библиотеки из data/games.json."""
    games_list, _, sessions_list = load_library(settings.DATA_DIR)
    context = {
        "games": [
            (game, hours_played(sessions_list, game=game))
            for game in games_list
        ],
    }
    return render(request, "games/game_list.html", context)


def game_detail(request: HttpRequest, game_id: int) -> HttpResponse:
    """Страница /games/<id>/: карточка игры и прогресс игроков."""
    games_list, users_list, sessions_list = load_library(settings.DATA_DIR)
    game = find_game_by_id(games_list, game_id)
    context: dict[str, object] = {"game": game}
    if game is not None:
        context["players"] = game_progress(sessions_list, users_list, game)
        context["sessions"] = active_sessions(sessions_list, game=game)
    return render(
        request,
        "games/game_detail.html",
        context,
        status=404 if game is None else 200,
    )
