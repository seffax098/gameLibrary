"""Тесты класса GameSession и функций работы с игровыми сессиями."""

from datetime import date

import pytest

from models import Game, GameSession, User
from models.sessions import (
    active_sessions,
    cancel_session,
    find_session_by_id,
    hours_played,
    is_day_free,
    log_session,
    remove_game_sessions,
)

DAY: date = date(2026, 9, 15)
NEXT_DAY: date = date(2026, 9, 16)


def test_session_creation(ivan: User, witcher: Game) -> None:
    """Сессия хранит ссылки на объекты пользователя и игры."""
    session = GameSession(1, ivan, witcher, DAY, 2.5)
    assert session.id == 1
    assert session.user is ivan
    assert session.game is witcher
    assert session.date == DAY
    assert session.hours == 2.5
    assert not session.is_cancelled


def test_session_gives_access_to_linked_objects(
    ivan: User,
    witcher: Game,
) -> None:
    """Данные пользователя и игры доступны через объект сессии."""
    session = GameSession(1, ivan, witcher, DAY, 2.5)
    assert session.user.email == "ivan@example.com"
    assert session.game.hours_total == 100.0


def test_session_rejects_non_positive_hours(
    ivan: User,
    witcher: Game,
) -> None:
    """Сессия без сыгранного времени не создаётся."""
    with pytest.raises(ValueError):
        GameSession(1, ivan, witcher, DAY, 0)


def test_session_str_shows_state(ivan: User, witcher: Game) -> None:
    """Строковое представление учитывает отмену сессии."""
    session = GameSession(3, ivan, witcher, DAY, 2.5)
    assert str(session) == (
        "Сессия 3: 15.09.2026, Иван Петров - The Witcher 3, 2.5 ч"
    )
    session.cancel()
    assert str(session).endswith("(отменена)")


def test_session_cancel(ivan: User, witcher: Game) -> None:
    """cancel() меняет состояние, повторная отмена - ValueError."""
    session = GameSession(1, ivan, witcher, DAY, 2.5)
    session.cancel()
    assert session.is_cancelled
    with pytest.raises(ValueError):
        session.cancel()


def test_is_cancelled_is_read_only(ivan: User, witcher: Game) -> None:
    """Состояние отмены нельзя изменить присваиванием."""
    session = GameSession(1, ivan, witcher, DAY, 2.5)
    with pytest.raises(AttributeError):
        setattr(session, "is_cancelled", True)


def test_log_session_adds_object(ivan: User, witcher: Game) -> None:
    """log_session() создаёт GameSession и добавляет его в коллекцию."""
    sessions: list[GameSession] = []
    session = log_session(sessions, ivan, witcher, DAY, 2.5)
    assert session is not None
    assert sessions == [session]
    assert session.user is ivan
    assert session.game is witcher


def test_second_session_same_day_is_not_created(
    ivan: User,
    witcher: Game,
) -> None:
    """Вторая активная сессия по игре за тот же день не создаётся."""
    sessions: list[GameSession] = []
    log_session(sessions, ivan, witcher, DAY, 2.5)
    assert not is_day_free(sessions, ivan, witcher, DAY)
    assert log_session(sessions, ivan, witcher, DAY, 1.0) is None
    assert len(sessions) == 1


def test_other_user_or_game_can_use_same_day(
    ivan: User,
    anna: User,
    witcher: Game,
    celeste: Game,
) -> None:
    """Правило одного дня действует для пары «пользователь - игра»."""
    sessions: list[GameSession] = []
    log_session(sessions, ivan, witcher, DAY, 2.5)
    assert log_session(sessions, anna, witcher, DAY, 1.0) is not None
    assert log_session(sessions, ivan, celeste, DAY, 1.0) is not None
    assert log_session(sessions, ivan, witcher, NEXT_DAY, 1.0) is not None


def test_cancelled_session_frees_day(ivan: User, witcher: Game) -> None:
    """После отмены день снова свободен, номер сессии не повторяется."""
    sessions: list[GameSession] = []
    first = log_session(sessions, ivan, witcher, DAY, 2.5)
    assert first is not None
    cancel_session(sessions, first.id)
    assert is_day_free(sessions, ivan, witcher, DAY)
    second = log_session(sessions, ivan, witcher, DAY, 3.0)
    assert second is not None
    assert second.id == 2
    assert len(sessions) == 2


def test_cancel_session_keeps_object(ivan: User, witcher: Game) -> None:
    """Отменённая сессия остаётся в коллекции."""
    sessions: list[GameSession] = []
    session = log_session(sessions, ivan, witcher, DAY, 2.5)
    assert session is not None
    assert cancel_session(sessions, session.id) is session
    assert session in sessions
    assert session.is_cancelled
    assert not active_sessions(sessions)


def test_cancel_unknown_session_raises_key_error() -> None:
    """Отмена несуществующей сессии вызывает KeyError."""
    with pytest.raises(KeyError):
        cancel_session([], 1)


def test_find_session_by_id(ivan: User, witcher: Game) -> None:
    """Сессия находится по идентификатору, иначе возвращается None."""
    sessions: list[GameSession] = []
    session = log_session(sessions, ivan, witcher, DAY, 2.5)
    assert session is not None
    assert find_session_by_id(sessions, session.id) is session
    assert find_session_by_id(sessions, 99) is None


def test_hours_played_counts_active_sessions(
    ivan: User,
    anna: User,
    witcher: Game,
    celeste: Game,
) -> None:
    """Часы считаются по пользователю, игре и только по активным."""
    sessions: list[GameSession] = []
    log_session(sessions, ivan, witcher, DAY, 2.0)
    log_session(sessions, ivan, witcher, NEXT_DAY, 3.0)
    log_session(sessions, anna, witcher, DAY, 4.0)
    cancelled = log_session(sessions, ivan, celeste, DAY, 6.0)
    assert cancelled is not None
    cancelled.cancel()
    assert hours_played(sessions, user=ivan, game=witcher) == 5.0
    assert hours_played(sessions, game=witcher) == 9.0
    assert hours_played(sessions, user=ivan) == 5.0
    assert hours_played(sessions) == 9.0


def test_remove_game_sessions(
    ivan: User,
    witcher: Game,
    celeste: Game,
) -> None:
    """При удалении игры удаляются только её сессии."""
    sessions: list[GameSession] = []
    log_session(sessions, ivan, witcher, DAY, 2.0)
    log_session(sessions, ivan, witcher, NEXT_DAY, 3.0)
    log_session(sessions, ivan, celeste, DAY, 1.0)
    assert remove_game_sessions(sessions, witcher) == 2
    assert [session.game for session in sessions] == [celeste]
