"""Тесты функций работы с игровыми сессиями и прогрессом."""

from datetime import date

import pytest

from sessions import (
    calculate_progress,
    cancel_session,
    get_status,
    hours_played,
    is_day_free,
    log_session,
    make_progress_bar,
)


def test_is_day_free() -> None:
    """Без сессий любой день свободен."""
    sessions: list[dict] = []
    assert is_day_free(sessions, 1, date(2026, 9, 15))


def test_duplicate_session_forbidden() -> None:
    """Вторая сессия по игре на ту же дату запрещена."""
    sessions: list[dict] = []
    log_session(sessions, 1, date(2026, 9, 15), 2.5)
    assert not is_day_free(sessions, 1, date(2026, 9, 15))
    with pytest.raises(ValueError):
        log_session(sessions, 1, date(2026, 9, 15), 1.0)


def test_hours_played_sums_only_one_game() -> None:
    """Часы суммируются только по выбранной игре."""
    sessions: list[dict] = []
    log_session(sessions, 1, date(2026, 9, 15), 2.0)
    log_session(sessions, 1, date(2026, 9, 16), 3.0)
    log_session(sessions, 2, date(2026, 9, 16), 4.0)
    assert hours_played(sessions, 1) == 5.0


def test_cancel_session() -> None:
    """Сессия отменяется, повторная отмена вызывает KeyError."""
    sessions: list[dict] = []
    session = log_session(sessions, 1, date(2026, 9, 15), 2.0)
    cancel_session(sessions, session["id"])
    assert not sessions
    with pytest.raises(KeyError):
        cancel_session(sessions, session["id"])


def test_calculate_progress_is_limited_by_hundred() -> None:
    """Прогресс считается в процентах и не превышает 100."""
    assert calculate_progress(5.0, 10.0) == 50.0
    assert calculate_progress(20.0, 10.0) == 100.0


def test_get_status() -> None:
    """Статус зависит от часов и прогресса."""
    assert get_status(0.0, 0.0) == "Не начата"
    assert get_status(5.0, 50.0) == "В процессе"
    assert get_status(10.0, 100.0) == "Пройдена"


def test_make_progress_bar() -> None:
    """Шкала прогресса пуста при 0 и полна при 100."""
    assert make_progress_bar(0.0) == "-" * 10
    assert make_progress_bar(100.0) == "#" * 10
