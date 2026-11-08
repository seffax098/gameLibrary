"""Страницы игровой библиотеки."""

import re

from django.db.models import Q, QuerySet, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from games.models import Game
from gamesessions.models import GameSession, Player
from models import Progress
from models.games import FIRST_GAME_YEAR


def _int_param(request: HttpRequest, name: str, default: int) -> int:
    """Вернуть числовой GET-параметр или значение по умолчанию."""
    try:
        return int(request.GET.get(name, ""))
    except ValueError:
        return default


def games(request: HttpRequest) -> HttpResponse:
    """Список игр, включая игры без сыгранных часов."""
    games_list = Game.objects.annotate(
        played=Sum(
            "sessions__hours", filter=Q(sessions__is_cancelled=False),
            default=0,
        ),
    ).order_by("pk")
    return render(request, "games/game_list.html", {"games": games_list})


def game_detail(request: HttpRequest, game_id: int) -> HttpResponse:
    """Карточка игры, активные сессии и прогресс всех игроков."""
    try:
        game = Game.objects.get(pk=game_id).as_library_game()
    except Game.DoesNotExist:
        return render(
            request, "games/game_detail.html", {"game": None}, status=404
        )

    players = Player.objects.annotate(
        played=Sum(
            "sessions__hours",
            filter=Q(sessions__game_id=game_id, sessions__is_cancelled=False),
            default=0,
        )
    ).order_by("pk")
    sessions = GameSession.objects.filter(
        game_id=game_id, is_cancelled=False
    ).select_related("player").order_by("session_date", "pk")
    context = {
        "game": game,
        "players": [
            Progress(player.as_library_user(), game, player.played)
            for player in players
        ],
        "sessions": sessions,
    }
    return render(request, "games/game_detail.html", context)


def game_search(request: HttpRequest) -> HttpResponse:
    """Поиск игры по названию, платформе, году и оценке."""
    title = request.GET.get("q", "").strip()[:255]
    platform = request.GET.get("platform", "")
    year_from = _int_param(request, "year_from", FIRST_GAME_YEAR)
    rating_from = _int_param(request, "rating_from", 0)
    platforms = Game.objects.order_by("platform").values_list(
        "platform", flat=True
    ).distinct()

    found = Game.objects.filter(release_year__gte=year_from)
    if platform:
        found = found.filter(platform=platform)
    if rating_from > 0:
        found = found.filter(rating__gte=rating_from)
    if title:
        # SQLite LIKE игнорирует регистр только для символов ASCII.
        found = found.filter(title__iregex=re.escape(title))

    context = {
        "games": found.order_by("-rating", "title", "pk"),
        "platforms": platforms,
        "q": title,
        "platform": platform,
        "year_from": request.GET.get("year_from", ""),
        "rating_from": request.GET.get("rating_from", ""),
    }
    return render(request, "games/game_search.html", context)


def unplayed_games(request: HttpRequest) -> HttpResponse:
    """Игры, в которых у выбранного игрока нет активных сессий."""
    users = list(Player.objects.order_by("name", "pk"))
    user_id = _int_param(request, "user", 0)
    player = next((user for user in users if user.pk == user_id), None)
    games_list: QuerySet[Game] | list[Game] = []
    if player is not None:
        played_ids = GameSession.objects.filter(
            player=player, is_cancelled=False
        ).values("game_id")
        games_list = Game.objects.exclude(pk__in=played_ids).order_by(
            "title", "pk"
        )
    return render(request, "games/game_unplayed.html", {
        "users": users, "player": player, "games": games_list,
    })
