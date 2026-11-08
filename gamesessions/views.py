"""Список и карточка игровых сессий."""

import re

from django import forms
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from games.models import Game
from gamesessions.models import GameSession, Player
from models import Progress

SESSION_ORDER = {
    "date": ("Дата ↑", "session_date"),
    "-date": ("Дата ↓", "-session_date"),
    "game": ("Игра", "game__title"),
    "player": ("Игрок", "player__name"),
    "-hours": ("Сыгранные часы ↓", "-hours"),
}
SESSION_SORT_CHOICES = [
    (key, label) for key, (label, _) in SESSION_ORDER.items()
]


class SessionFilters(forms.Form):
    """Проверка параметров поиска, фильтрации и сортировки."""

    q = forms.CharField(required=False, max_length=255)
    game = forms.IntegerField(required=False, min_value=1, max_value=2**63 - 1)
    player = forms.IntegerField(
        required=False, min_value=1, max_value=2**63 - 1
    )
    date = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    sort = forms.ChoiceField(required=False, choices=SESSION_SORT_CHOICES)


def sessions(request: HttpRequest) -> HttpResponse:
    """История сессий с поиском, фильтрами и пагинацией."""
    form = SessionFilters(request.GET)
    form.is_valid()
    filters = form.cleaned_data
    sessions_list = GameSession.objects.select_related("player", "game")
    if query := filters.get("q"):
        pattern = re.escape(query)
        sessions_list = sessions_list.filter(
            Q(game__title__iregex=pattern) | Q(player__name__iregex=pattern)
        )
    if game_id := filters.get("game"):
        sessions_list = sessions_list.filter(game_id=game_id)
    if player_id := filters.get("player"):
        sessions_list = sessions_list.filter(player_id=player_id)
    if session_date := filters.get("date"):
        sessions_list = sessions_list.filter(session_date=session_date)

    sort = filters.get("sort") or "date"
    sessions_list = sessions_list.order_by(SESSION_ORDER[sort][1], "pk")
    page = Paginator(sessions_list, 5).get_page(request.GET.get("page"))
    context = {
        "sessions": page,
        "games": Game.objects.order_by("title", "pk"),
        "players": Player.objects.order_by("name", "pk"),
        "q": filters.get("q", ""),
        "selected_game": filters.get("game"),
        "selected_player": filters.get("player"),
        "selected_date": filters.get("date"),
        "sort": sort,
        "sort_options": SESSION_SORT_CHOICES,
    }
    return render(request, "gamesessions/session_list.html", context)


def session_detail(request: HttpRequest, session_id: int) -> HttpResponse:
    """Карточка сессии и прогресс игрока в связанной игре."""
    try:
        session = GameSession.objects.select_related("game", "player").get(
            pk=session_id
        )
    except GameSession.DoesNotExist:
        return render(
            request, "gamesessions/session_detail.html",
            {"session": None}, status=404,
        )

    totals = GameSession.objects.filter(
        player_id=session.player_id, game_id=session.game_id,
        is_cancelled=False,
    ).aggregate(hours=Sum("hours", default=0))
    progress = Progress(
        session.player.as_library_user(),
        session.game.as_library_game(),
        totals["hours"],
    )
    return render(request, "gamesessions/session_detail.html", {
        "session": session, "progress": progress,
    })
