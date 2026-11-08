"""View-функции приложения gamesessions.

Данные берутся из базы SQLite (settings.LIBRARY_DB) SQL-запросами,
сохранёнными также в sql/queries.sql.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one
from models import Game, Progress, User


def sessions(request: HttpRequest) -> HttpResponse:
    """Страница /sessions/: все сессии с игроком и игрой по датам."""
    sessions_list = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            sessions.id,
            strftime('%d.%m.%Y', sessions.session_date) AS played_on,
            sessions.hours,
            sessions.is_cancelled,
            users.name AS user_name,
            games.id AS game_id,
            games.title AS game_title
        FROM sessions
        JOIN users
            ON sessions.user_id = users.id
        JOIN games
            ON sessions.game_id = games.id
        ORDER BY sessions.session_date, sessions.id
        """,
    )
    return render(
        request,
        "gamesessions/session_list.html",
        {"sessions": sessions_list},
    )


def session_detail(
    request: HttpRequest,
    session_id: int,
) -> HttpResponse:
    """Страница /sessions/<id>/: карточка сессии и прогресс игрока."""
    session = fetch_one(
        settings.LIBRARY_DB,
        """
        SELECT
            sessions.id,
            strftime('%d.%m.%Y', sessions.session_date) AS played_on,
            sessions.hours,
            sessions.is_cancelled,
            users.id AS user_id,
            users.name AS user_name,
            users.email AS user_email,
            games.id AS game_id,
            games.title AS game_title,
            games.genre AS game_genre,
            games.platform AS game_platform,
            games.release_year AS game_year,
            games.hours_total AS game_hours_total,
            games.rating AS game_rating
        FROM sessions
        JOIN users
            ON sessions.user_id = users.id
        JOIN games
            ON sessions.game_id = games.id
        WHERE sessions.id = ?
        """,
        [session_id],
    )
    if session is None:
        return render(
            request,
            "gamesessions/session_detail.html",
            {"session": None},
            status=404,
        )
    played = fetch_one(
        settings.LIBRARY_DB,
        """
        SELECT
            COALESCE(SUM(hours), 0) AS hours
        FROM sessions
        WHERE user_id = ?
            AND game_id = ?
            AND is_cancelled = 0
        """,
        [session["user_id"], session["game_id"]],
    )
    assert played is not None
    user = User(
        session["user_id"], session["user_name"], session["user_email"]
    )
    game = Game(
        session["game_id"],
        session["game_title"],
        session["game_genre"],
        session["game_platform"],
        session["game_year"],
        session["game_hours_total"],
        session["game_rating"] or 0,
    )
    progress = Progress(user, game, played["hours"])
    return render(
        request,
        "gamesessions/session_detail.html",
        {"session": session, "progress": progress},
    )
