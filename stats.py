"""Функции расчёта статистики игровой библиотеки."""

import sessions as sessions_module


def count_by_platform(games: dict[int, dict]) -> dict[str, int]:
    """Подсчитать количество игр на каждой платформе."""
    counts: dict[str, int] = {}
    for game in games.values():
        platform = game["platform"]
        counts[platform] = counts.get(platform, 0) + 1
    return counts


def count_by_status(
    games: dict[int, dict],
    sessions: list[dict],
) -> dict[str, int]:
    """Подсчитать количество игр в каждом статусе прохождения."""
    counts = {"Не начата": 0, "В процессе": 0, "Пройдена": 0}
    for game_id, game in games.items():
        progress = sessions_module.get_game_progress(
            sessions, game_id, game["hours_total"]
        )
        counts[progress["status"]] += 1
    return counts


def average_rating(games: dict[int, dict]) -> float:
    """Вычислить среднюю оценку по играм с выставленной оценкой."""
    ratings = [
        game["rating"] for game in games.values() if game["rating"]
    ]
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)


def total_hours(sessions: list[dict]) -> float:
    """Подсчитать суммарное время всех игровых сессий."""
    return sum(session["hours"] for session in sessions)


def top_games_by_hours(
    games: dict[int, dict],
    sessions: list[dict],
    limit: int = 3,
) -> list[tuple[str, float]]:
    """Вернуть игры с наибольшим наигранным временем."""
    played = [
        (game["title"], sessions_module.hours_played(sessions, game_id))
        for game_id, game in games.items()
    ]
    played.sort(key=lambda item: -item[1])
    return [item for item in played[:limit] if item[1] > 0]


def library_stats(
    games: dict[int, dict],
    sessions: list[dict],
) -> dict:
    """Собрать сводную статистику библиотеки."""
    genres = {game["genre"] for game in games.values()}
    return {
        "games": len(games),
        "sessions": len(sessions),
        "hours": total_hours(sessions),
        "average_rating": average_rating(games),
        "genres": sorted(genres),
        "platforms": count_by_platform(games),
        "statuses": count_by_status(games, sessions),
        "top": top_games_by_hours(games, sessions),
    }
