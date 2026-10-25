"""View-функции приложения homepage.

Сводка и статистика вычисляются агрегатными SQL-запросами к базе
SQLite (settings.LIBRARY_DB); запросы сохранены также в
sql/queries.sql.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one

DEFAULT_MIN_HOURS: float = 10.0


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание библиотеки, сводка и рейтинги."""
    summary = fetch_one(
        settings.LIBRARY_DB,
        """
        SELECT
            (SELECT COUNT(*) FROM games) AS games_count,
            (SELECT COUNT(*) FROM users) AS users_count,
            (SELECT COUNT(*) FROM sessions WHERE is_cancelled = 0)
                AS sessions_count,
            (SELECT COUNT(*) FROM sessions WHERE is_cancelled = 1)
                AS cancelled_count,
            (SELECT COALESCE(SUM(hours), 0) FROM sessions
                WHERE is_cancelled = 0) AS hours_played,
            (SELECT AVG(rating) FROM games) AS average_rating
        """,
    )
    top_games = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            games.id,
            games.title,
            SUM(sessions.hours) AS hours
        FROM games
        JOIN sessions
            ON sessions.game_id = games.id
        WHERE sessions.is_cancelled = 0
        GROUP BY games.id, games.title
        ORDER BY hours DESC
        LIMIT 3
        """,
    )
    top_players = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            users.id,
            users.name,
            SUM(sessions.hours) AS hours
        FROM users
        JOIN sessions
            ON sessions.user_id = users.id
        WHERE sessions.is_cancelled = 0
        GROUP BY users.id, users.name
        ORDER BY hours DESC
        LIMIT 3
        """,
    )
    context = {
        "summary": summary,
        "top_games": top_games,
        "top_players": top_players,
    }
    return render(request, "homepage/index.html", context)


def statistics(request: HttpRequest) -> HttpResponse:
    """Страница /statistics/: жанры, платформы, игроки, популярные игры.

    Порог часов для популярных игр задаётся параметром min_hours и
    передаётся в условие HAVING параметром ?.
    """
    try:
        min_hours = float(request.GET.get("min_hours", DEFAULT_MIN_HOURS))
    except ValueError:
        min_hours = DEFAULT_MIN_HOURS
    genres = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            genre,
            COUNT(*) AS games_count,
            AVG(rating) AS average_rating
        FROM games
        GROUP BY genre
        ORDER BY games_count DESC, genre
        """,
    )
    platforms = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            platform,
            COUNT(*) AS games_count,
            MIN(release_year) AS first_year,
            MAX(release_year) AS last_year
        FROM games
        GROUP BY platform
        ORDER BY games_count DESC, platform
        """,
    )
    players = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            users.id,
            users.name,
            COUNT(sessions.id) AS sessions_count,
            COUNT(DISTINCT sessions.game_id) AS games_count,
            COALESCE(SUM(sessions.hours), 0) AS hours
        FROM users
        LEFT JOIN sessions
            ON sessions.user_id = users.id
            AND sessions.is_cancelled = 0
        GROUP BY users.id, users.name
        ORDER BY hours DESC, users.name
        """,
    )
    popular = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            games.id,
            games.title,
            COUNT(sessions.id) AS sessions_count,
            SUM(sessions.hours) AS hours
        FROM games
        JOIN sessions
            ON sessions.game_id = games.id
        WHERE sessions.is_cancelled = 0
        GROUP BY games.id, games.title
        HAVING SUM(sessions.hours) >= ?
        ORDER BY hours DESC
        """,
        [min_hours],
    )
    context = {
        "genres": genres,
        "platforms": platforms,
        "players": players,
        "popular": popular,
        "min_hours": min_hours,
    }
    return render(request, "homepage/statistics.html", context)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Обработчик ошибки 404 для всего проекта (handler404)."""
    return render(request, "404.html", status=404)
