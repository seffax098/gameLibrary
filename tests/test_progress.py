"""Тесты класса Progress и расчёта личного прогресса."""

from datetime import date

import pytest

from models import Game, GameSession, Progress, User
from models.sessions import get_progress, log_session


def test_progress_links_user_and_game(ivan: User, witcher: Game) -> None:
    """Прогресс хранит ссылки на пользователя и игру."""
    progress = Progress(ivan, witcher, 10.0)
    assert progress.user is ivan
    assert progress.game is witcher
    assert progress.hours == 10.0


def test_progress_percent_is_limited_by_hundred(
    ivan: User,
    witcher: Game,
) -> None:
    """Процент считается от времени прохождения и не превышает 100."""
    assert Progress(ivan, witcher, 50.0).percent == 50.0
    assert Progress(ivan, witcher, 150.0).percent == 100.0


def test_progress_status(ivan: User, witcher: Game) -> None:
    """Статус зависит от сыгранных часов и процента прохождения."""
    assert Progress(ivan, witcher, 0.0).status == "Не начата"
    assert Progress(ivan, witcher, 50.0).status == "В процессе"
    assert Progress(ivan, witcher, 100.0).status == "Пройдена"


def test_progress_bar_and_hours_left(ivan: User, witcher: Game) -> None:
    """Шкала и оставшееся время вычисляются по сыгранным часам."""
    assert Progress(ivan, witcher, 0.0).progress_bar == "-" * 10
    assert Progress(ivan, witcher, 100.0).progress_bar == "#" * 10
    assert Progress(ivan, witcher, 30.0).hours_left == 70.0
    assert Progress(ivan, witcher, 130.0).hours_left == 0.0


def test_progress_str(ivan: User, witcher: Game) -> None:
    """Строковое представление содержит шкалу, процент и статус."""
    progress = Progress(ivan, witcher, 50.0)
    assert str(progress) == "[#####-----] 50% - В процессе"


def test_progress_rejects_negative_hours(ivan: User, witcher: Game) -> None:
    """Отрицательное время вызывает ValueError."""
    with pytest.raises(ValueError):
        Progress(ivan, witcher, -1.0)


def test_get_progress_is_personal(
    ivan: User,
    anna: User,
    celeste: Game,
) -> None:
    """Прогресс каждого пользователя считается по его сессиям."""
    sessions: list[GameSession] = []
    log_session(sessions, ivan, celeste, date(2026, 9, 15), 12.0)
    log_session(sessions, anna, celeste, date(2026, 9, 15), 3.0)
    assert get_progress(sessions, ivan, celeste).status == "Пройдена"
    assert get_progress(sessions, anna, celeste).percent == 25.0
