"""Главная страница и статистика игровой библиотеки."""

from math import isfinite

from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from games.models import Game
from gamesessions.models import PLAYED_STATUSES, GameSession, Player

DEFAULT_MIN_HOURS = 10.0


def index(request: HttpRequest) -> HttpResponse:
    """Сводка библиотеки и тройки лидеров по сыгранным часам."""
    summary = Game.objects.aggregate(
        games_count=Count("pk"), average_rating=Avg("rating")
    )
    summary["users_count"] = Player.objects.count()
    summary.update(GameSession.objects.aggregate(
        sessions_count=Count("pk", filter=Q(status=GameSession.Status.ACTIVE)),
        cancelled_count=Count(
            "pk", filter=Q(status=GameSession.Status.CANCELLED),
        ),
        completed_count=Count(
            "pk", filter=Q(status=GameSession.Status.COMPLETED),
        ),
        hours_played=Sum(
            "hours", filter=Q(status__in=PLAYED_STATUSES), default=0,
        ),
    ))
    played = Q(sessions__status__in=PLAYED_STATUSES)
    top_games = Game.objects.filter(played).annotate(
        hours=Sum("sessions__hours")
    ).order_by("-hours", "pk")[:3]
    top_players = Player.objects.filter(played).annotate(
        hours=Sum("sessions__hours")
    ).order_by("-hours", "pk")[:3]

    return render(request, "homepage/index.html", {
        "summary": summary, "top_games": top_games, "top_players": top_players,
        "library_games_count": summary["games_count"],
    })


def statistics(request: HttpRequest) -> HttpResponse:
    """Статистика по жанрам, платформам, игрокам и популярным играм."""
    try:
        min_hours = float(request.GET.get("min_hours", DEFAULT_MIN_HOURS))
    except ValueError:
        min_hours = DEFAULT_MIN_HOURS
    if not isfinite(min_hours):
        min_hours = DEFAULT_MIN_HOURS

    genres = Game.objects.values("genre").annotate(
        games_count=Count("pk"), average_rating=Avg("rating")
    ).order_by("-games_count", "genre")
    platforms = Game.objects.values("platform").annotate(
        games_count=Count("pk"), first_year=Min("release_year"),
        last_year=Max("release_year"),
    ).order_by("-games_count", "platform")

    played = Q(sessions__status__in=PLAYED_STATUSES)
    players = Player.objects.values("id", "name").annotate(
        sessions_count=Count(
            "sessions", filter=Q(sessions__status=GameSession.Status.ACTIVE),
        ),
        completed_count=Count(
            "sessions",
            filter=Q(sessions__status=GameSession.Status.COMPLETED),
        ),
        cancelled_count=Count(
            "sessions",
            filter=Q(sessions__status=GameSession.Status.CANCELLED),
        ),
        games_count=Count("sessions__game", distinct=True, filter=played),
        hours=Sum("sessions__hours", filter=played, default=0),
    ).order_by("-hours", "name", "id")
    popular = Game.objects.filter(played).values(
        "id", "title", "slug"
    ).annotate(
        sessions_count=Count("sessions"), hours=Sum("sessions__hours")
    ).filter(hours__gte=min_hours).order_by("-hours", "id")

    return render(request, "homepage/statistics.html", {
        "genres": genres, "platforms": platforms, "players": players,
        "popular": popular, "min_hours": min_hours,
    })


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Обработчик ошибки 404 для всего проекта."""
    return render(request, "404.html", status=404)
