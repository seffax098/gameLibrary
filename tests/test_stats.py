"""Тесты статистики игровой библиотеки."""

from datetime import date

from models import Game, GameSession, User
from models.sessions import log_session
from stats import (
    average_rating,
    count_by_platform,
    count_by_status,
    library_stats,
)

DAY: date = date(2026, 9, 15)


def make_sessions(
    ivan: User,
    anna: User,
    witcher: Game,
    celeste: Game,
) -> list[GameSession]:
    """Иван прошёл Celeste, Анна играет в The Witcher 3."""
    sessions: list[GameSession] = []
    log_session(sessions, ivan, celeste, DAY, 12.0)
    log_session(sessions, anna, witcher, DAY, 10.0)
    cancelled = log_session(sessions, ivan, witcher, DAY, 5.0)
    assert cancelled is not None
    cancelled.cancel()
    return sessions


def test_library_stats(
    ivan: User,
    anna: User,
    witcher: Game,
    celeste: Game,
) -> None:
    """Статистика учитывает игры, пользователей и активные сессии."""
    sessions = make_sessions(ivan, anna, witcher, celeste)
    report = library_stats([witcher, celeste], [ivan, anna], sessions)
    assert report["games"] == 2
    assert report["users"] == 2
    assert report["sessions"] == 2
    assert report["cancelled"] == 1
    assert report["hours"] == 22.0
    assert report["top"] == [(celeste, 12.0), (witcher, 10.0)]
    assert report["players"] == [(ivan, 12.0), (anna, 10.0)]


def test_count_by_status_is_personal(
    ivan: User,
    anna: User,
    witcher: Game,
    celeste: Game,
) -> None:
    """Статусы игр считаются отдельно для каждого пользователя."""
    games = [witcher, celeste]
    sessions = make_sessions(ivan, anna, witcher, celeste)
    assert count_by_status(games, sessions, ivan) == {
        "Не начата": 1,
        "В процессе": 0,
        "Пройдена": 1,
    }
    assert count_by_status(games, sessions, anna)["В процессе"] == 1


def test_average_rating_ignores_unrated(witcher: Game) -> None:
    """Игры без оценки не влияют на среднюю оценку."""
    unrated = Game(3, "God of War", "Экшен", "PlayStation", 2018, 25.0)
    assert average_rating([witcher, unrated]) == 10.0
    assert average_rating([unrated]) == 0.0


def test_count_by_platform(witcher: Game, celeste: Game) -> None:
    """Игры подсчитываются по платформам."""
    switch = Game(3, "Hades", "Roguelike", "Nintendo Switch", 2020, 40.0)
    assert count_by_platform([witcher, celeste, switch]) == {
        "PC": 2,
        "Nintendo Switch": 1,
    }
