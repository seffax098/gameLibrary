"""View-функции приложения games.

Данные берутся из базы SQLite (settings.LIBRARY_DB) SQL-запросами,
сохранёнными также в sql/queries.sql. Значения от пользователя
передаются в запрос параметрами ?, а не вставляются в текст SQL.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one
from models import Game, Progress, User
from models.games import FIRST_GAME_YEAR


def _int_param(request: HttpRequest, name: str, default: int) -> int:
    """Целое число из параметра GET; пустое или неверное - default."""
    try:
        return int(request.GET.get(name, ""))
    except ValueError:
        return default


def games(request: HttpRequest) -> HttpResponse:
    """Страница /games/: игры и часы, сыгранные всеми игроками."""
    games_list = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            games.id,
            games.title,
            games.genre,
            games.platform,
            games.release_year,
            games.rating,
            COALESCE(SUM(sessions.hours), 0) AS played
        FROM games
        LEFT JOIN sessions
            ON sessions.game_id = games.id
            AND sessions.is_cancelled = 0
        GROUP BY games.id
        ORDER BY games.id
        """,
    )
    return render(request, "games/game_list.html", {"games": games_list})


def game_detail(request: HttpRequest, game_id: int) -> HttpResponse:
    """Страница /games/<id>/: карточка игры и прогресс игроков.

    Строки базы превращаются в объекты Game, User и Progress: эпоху,
    описание оценки, процент и статус прохождения вычисляет модель.
    """
    row = fetch_one(
        settings.LIBRARY_DB,
        """
        SELECT
            id,
            title,
            genre,
            platform,
            release_year,
            hours_total,
            rating
        FROM games
        WHERE id = ?
        """,
        [game_id],
    )
    if row is None:
        return render(
            request, "games/game_detail.html", {"game": None}, status=404
        )
    game = Game.from_data(dict(row))
    players = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            users.id,
            users.name,
            users.email,
            COALESCE(SUM(sessions.hours), 0) AS hours
        FROM users
        LEFT JOIN sessions
            ON sessions.user_id = users.id
            AND sessions.game_id = ?
            AND sessions.is_cancelled = 0
        GROUP BY users.id, users.name, users.email
        ORDER BY users.id
        """,
        [game_id],
    )
    sessions = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            sessions.id,
            strftime('%d.%m.%Y', sessions.session_date) AS played_on,
            sessions.hours,
            users.name AS user_name
        FROM sessions
        JOIN users
            ON sessions.user_id = users.id
        WHERE sessions.game_id = ?
            AND sessions.is_cancelled = 0
        ORDER BY sessions.session_date, sessions.id
        """,
        [game_id],
    )
    context = {
        "game": game,
        "players": [
            Progress(User.from_data(dict(player)), game, player["hours"])
            for player in players
        ],
        "sessions": sessions,
    }
    return render(request, "games/game_detail.html", context)


def game_search(request: HttpRequest) -> HttpResponse:
    """Страница /games/search/: поиск игр по платформе, году и оценке.

    Пустая платформа означает «любая»: условие (? = '' OR platform = ?)
    получает значение платформы дважды.
    """
    platform = request.GET.get("platform", "")
    year_from = _int_param(request, "year_from", FIRST_GAME_YEAR)
    rating_from = _int_param(request, "rating_from", 0)
    platforms = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT DISTINCT platform
        FROM games
        ORDER BY platform
        """,
    )
    found = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            id,
            title,
            genre,
            platform,
            release_year,
            rating
        FROM games
        WHERE (? = '' OR platform = ?)
            AND release_year >= ?
            AND COALESCE(rating, 0) >= ?
        ORDER BY rating DESC, title
        """,
        [platform, platform, year_from, rating_from],
    )
    context = {
        "games": found,
        "platforms": [row["platform"] for row in platforms],
        "platform": platform,
        "year_from": request.GET.get("year_from", ""),
        "rating_from": request.GET.get("rating_from", ""),
    }
    return render(request, "games/game_search.html", context)


def unplayed_games(request: HttpRequest) -> HttpResponse:
    """Страница /games/unplayed/: игры, в которые игрок ещё не играл.

    Запрос к играм выполняется, только если выбран существующий игрок.
    """
    users = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT
            id,
            name,
            email
        FROM users
        ORDER BY name
        """,
    )
    user_id = _int_param(request, "user", 0)
    player = next((user for user in users if user["id"] == user_id), None)
    games_list = []
    if player is not None:
        games_list = fetch_all(
            settings.LIBRARY_DB,
            """
            SELECT
                games.id,
                games.title,
                games.genre,
                games.platform,
                games.hours_total
            FROM games
            WHERE games.id NOT IN (
                SELECT sessions.game_id
                FROM sessions
                WHERE sessions.user_id = ?
                    AND sessions.is_cancelled = 0
            )
            ORDER BY games.title
            """,
            [user_id],
        )
    context = {
        "users": users,
        "player": player,
        "games": games_list,
    }
    return render(request, "games/game_unplayed.html", context)
