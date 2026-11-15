"""Страницы игровой библиотеки."""

import re

from django import forms
from django.db.models import Q, QuerySet, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from games.models import Game
from gamesessions.models import PLAYED_STATUSES, GameSession, Player
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
            "sessions__hours", filter=Q(sessions__status__in=PLAYED_STATUSES),
            default=0,
        ),
    ).order_by("pk")
    return render(request, "games/game_list.html", {"games": games_list})


def game_detail(
    request: HttpRequest, game_id: int | None = None, slug: str | None = None,
) -> HttpResponse:
    """Карточка игры, сыгранные сессии и прогресс всех игроков."""
    try:
        key = {"slug": slug} if slug is not None else {"pk": game_id}
        entry = Game.objects.get(**key)
    except Game.DoesNotExist:
        return render(
            request, "games/game_detail.html", {"game": None}, status=404
        )

    game = entry.as_library_game()
    players = Player.objects.annotate(
        played=Sum(
            "sessions__hours",
            filter=Q(
                sessions__game_id=game.id,
                sessions__status__in=PLAYED_STATUSES,
            ),
            default=0,
        )
    ).order_by("pk")
    sessions = GameSession.objects.played().filter(
        game_id=game.id
    ).select_related("player").order_by("session_date", "pk")
    context = {
        "game": game,
        "is_long": entry.is_long,
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
    """Игры без сыгранных сессий или без активной сессии на дату."""
    users = list(Player.objects.order_by("name", "pk"))
    user_id = _int_param(request, "user", 0)
    player = next((user for user in users if user.pk == user_id), None)
    date_form = AvailabilityDateForm(request.GET)
    valid_date = date_form.is_valid()
    selected_date = date_form.cleaned_data.get("date") if valid_date else None
    games_list: QuerySet[Game] | list[Game] = []
    if player is not None and valid_date:
        history = GameSession.objects.filter(player=player)
        excluded_sessions = (
            history.active().for_date(selected_date)
            if selected_date else history.played()
        )
        games_list = Game.objects.exclude(
            pk__in=excluded_sessions.values("game_id")
        ).order_by(
            "title", "pk"
        )
    return render(request, "games/game_unplayed.html", {
        "users": users, "player": player, "games": games_list,
        "selected_date": selected_date, "date_error": date_form.errors.get(
            "date"
        ),
    })


class AvailabilityDateForm(forms.Form):
    """Проверка необязательной даты в подборе игр."""

    date = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
