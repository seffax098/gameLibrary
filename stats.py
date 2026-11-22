"""Функции расчёта статистики игровой библиотеки."""

from models import Game, GameSession, User
from models import sessions as sessions_module
from models.progress import STATUSES


def count_by_platform(games: list[Game]) -> dict[str, int]:
    """Подсчитать количество игр на каждой платформе."""
    counts: dict[str, int] = {}
    for game in games:
        counts[game.platform] = counts.get(game.platform, 0) + 1
    return counts


def count_by_status(
    games: list[Game],
    sessions: list[GameSession],
    user: User,
) -> dict[str, int]:
    """Подсчитать игры библиотеки в каждом статусе для пользователя."""
    counts = dict.fromkeys(STATUSES, 0)
    for progress in sessions_module.user_progress(sessions, games, user):
        counts[progress.status] += 1
    return counts


def average_rating(games: list[Game]) -> float:
    """Вычислить среднюю оценку по играм с выставленной оценкой."""
    ratings = [game.rating for game in games if game.rating]
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)


def total_hours(sessions: list[GameSession]) -> float:
    """Подсчитать суммарное время всех активных игровых сессий."""
    return sessions_module.hours_played(sessions)


def top_games_by_hours(
    games: list[Game],
    sessions: list[GameSession],
    limit: int = 3,
) -> list[tuple[Game, float]]:
    """Вернуть игры с наибольшим временем всех пользователей."""
    played = [
        (game, sessions_module.hours_played(sessions, game=game))
        for game in games
    ]
    played.sort(key=lambda item: -item[1])
    return [item for item in played[:limit] if item[1] > 0]


def top_users_by_hours(
    users: list[User],
    sessions: list[GameSession],
    limit: int = 3,
) -> list[tuple[User, float]]:
    """Вернуть пользователей, которые играли больше всего."""
    played = [
        (user, sessions_module.hours_played(sessions, user=user))
        for user in users
    ]
    played.sort(key=lambda item: -item[1])
    return [item for item in played[:limit] if item[1] > 0]


def library_stats(
    games: list[Game],
    users: list[User],
    sessions: list[GameSession],
) -> dict:
    """Собрать сводную статистику библиотеки."""
    genres = {game.genre for game in games}
    return {
        "games": len(games),
        "users": len(users),
        "sessions": len(sessions_module.active_sessions(sessions)),
        "cancelled": sum(session.is_cancelled for session in sessions),
        "hours": total_hours(sessions),
        "average_rating": average_rating(games),
        "genres": sorted(genres),
        "platforms": count_by_platform(games),
        "top": top_games_by_hours(games, sessions),
        "players": top_users_by_hours(users, sessions),
    }
