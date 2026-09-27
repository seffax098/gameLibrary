"""Игровые сессии и функции работы с коллекцией сессий.

Сессия описывается классом ``GameSession`` и связывает пользователя
(объект ``User``) с игрой (объект ``Game``). У пользователя может быть
только одна активная сессия по игре за день. Отменённая сессия
остаётся в коллекции как история, но не учитывается в прогрессе и не
занимает день.
"""

from datetime import date

from .games import Game
from .progress import Progress
from .users import User

DATE_FORMAT: str = "%d.%m.%Y"


class GameSession:
    """Игровая сессия: сколько часов пользователь играл в игру за день."""

    def __init__(
        self,
        session_id: int,
        user: User,
        game: Game,
        session_date: date,
        hours: float,
        is_cancelled: bool = False,
    ) -> None:
        """Создать сессию, связав её с объектами пользователя и игры.

        При неположительном количестве часов возбуждается ValueError.
        """
        if hours <= 0:
            raise ValueError("Количество часов должно быть больше нуля.")
        self.id = session_id
        self.user = user
        self.game = game
        self.date = session_date
        self.hours = float(hours)
        self._is_cancelled = is_cancelled

    def __str__(self) -> str:
        """Вернуть описание сессии с учётом её состояния."""
        text = (
            f"Сессия {self.id}: {self.date.strftime(DATE_FORMAT)}, "
            f"{self.user.name} - {self.game.title}, {self.hours:.1f} ч"
        )
        if self._is_cancelled:
            text += " (отменена)"
        return text

    @property
    def is_cancelled(self) -> bool:
        """Признак отмены: доступен для чтения, меняется методом cancel()."""
        return self._is_cancelled

    def cancel(self) -> None:
        """Отменить сессию.

        Повторная отмена возбуждает исключение ValueError.
        """
        if self._is_cancelled:
            raise ValueError(f"Сессия {self.id} уже отменена.")
        self._is_cancelled = True

    def occupies_day(self, user: User, game: Game, session_date: date) -> bool:
        """Проверить, занимает ли сессия день пользователя по игре.

        День занимает только активная сессия того же пользователя по
        той же игре на ту же дату.
        """
        return (
            not self._is_cancelled
            and self.user.id == user.id
            and self.game.id == game.id
            and self.date == session_date
        )

    @classmethod
    def from_data(cls, data: dict, user: User, game: Game) -> "GameSession":
        """Создать сессию из набора данных и найденных объектов.

        В JSON хранятся идентификаторы пользователя и игры; сами
        объекты находит модуль storage и передаёт в этот метод.
        """
        return cls(
            int(data["id"]),
            user,
            game,
            date.fromisoformat(data["date"]),
            float(data["hours"]),
            bool(data.get("is_cancelled", False)),
        )

    def to_data(self) -> dict:
        """Вернуть данные сессии для JSON: связи заменяются на id."""
        return {
            "id": self.id,
            "user_id": self.user.id,
            "game_id": self.game.id,
            "date": self.date.isoformat(),
            "hours": self.hours,
            "is_cancelled": self._is_cancelled,
        }


def next_session_id(sessions: list[GameSession]) -> int:
    """Вернуть свободный идентификатор для новой сессии.

    Отменённые сессии остаются в коллекции, поэтому их номера не
    используются повторно.
    """
    if not sessions:
        return 1
    return max(session.id for session in sessions) + 1


def is_day_free(
    sessions: list[GameSession],
    user: User,
    game: Game,
    session_date: date,
) -> bool:
    """Проверить, может ли пользователь записать сессию по игре за день."""
    return not any(
        session.occupies_day(user, game, session_date) for session in sessions
    )


def log_session(
    sessions: list[GameSession],
    user: User,
    game: Game,
    session_date: date,
    hours: float,
) -> GameSession | None:
    """Создать сессию, добавить её в коллекцию и вернуть её.

    Если день уже занят активной сессией пользователя по этой игре,
    сессия не создаётся и возвращается None. Некорректное количество
    часов вызывает ValueError.
    """
    if not is_day_free(sessions, user, game, session_date):
        return None
    session = GameSession(
        next_session_id(sessions), user, game, session_date, hours
    )
    sessions.append(session)
    return session


def get_session(sessions: list[GameSession], session_id: int) -> GameSession:
    """Вернуть сессию по идентификатору.

    Если сессия не найдена, возбуждается исключение KeyError.
    """
    for session in sessions:
        if session.id == session_id:
            return session
    raise KeyError(f"Сессия с идентификатором {session_id} не найдена.")


def cancel_session(
    sessions: list[GameSession],
    session_id: int,
) -> GameSession:
    """Найти сессию, отменить её методом cancel() и вернуть её.

    Сессия не удаляется из коллекции: меняется только её состояние.
    """
    session = get_session(sessions, session_id)
    session.cancel()
    return session


def remove_game_sessions(sessions: list[GameSession], game: Game) -> int:
    """Удалить все сессии игры и вернуть количество удалённых.

    Используется при удалении игры из библиотеки: сессию без игры
    нельзя ни показать, ни сохранить.
    """
    remaining = [session for session in sessions if session.game.id != game.id]
    removed = len(sessions) - len(remaining)
    sessions[:] = remaining
    return removed


def active_sessions(
    sessions: list[GameSession],
    *,
    user: User | None = None,
    game: Game | None = None,
) -> list[GameSession]:
    """Вернуть активные сессии, упорядоченные по дате.

    Если передан пользователь или игра, остаются только их сессии.
    """
    selected = (
        session
        for session in sessions
        if not session.is_cancelled
        and (user is None or session.user.id == user.id)
        and (game is None or session.game.id == game.id)
    )
    return sorted(selected, key=lambda session: session.date)


def hours_played(
    sessions: list[GameSession],
    *,
    user: User | None = None,
    game: Game | None = None,
) -> float:
    """Подсчитать часы активных сессий пользователя и/или игры."""
    return sum(
        session.hours
        for session in active_sessions(sessions, user=user, game=game)
    )


def get_progress(
    sessions: list[GameSession],
    user: User,
    game: Game,
) -> Progress:
    """Вернуть прогресс пользователя в игре по его активным сессиям."""
    return Progress(user, game, hours_played(sessions, user=user, game=game))


def user_progress(
    sessions: list[GameSession],
    games: list[Game],
    user: User,
) -> list[Progress]:
    """Вернуть прогресс пользователя по каждой игре библиотеки."""
    return [get_progress(sessions, user, game) for game in games]


def game_progress(
    sessions: list[GameSession],
    users: list[User],
    game: Game,
) -> list[Progress]:
    """Вернуть прогресс каждого пользователя в выбранной игре."""
    return [get_progress(sessions, user, game) for user in users]
