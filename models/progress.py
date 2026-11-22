"""Прогресс прохождения игры пользователем.

Прогресс личный: он связывает конкретного пользователя с конкретной
игрой и вычисляется по часам его активных игровых сессий.
"""

from .games import Game
from .users import User

PROGRESS_BAR_LENGTH: int = 10
FULL_PROGRESS: float = 100.0

NOT_STARTED: str = "Не начата"
IN_PROGRESS: str = "В процессе"
COMPLETED: str = "Пройдена"
STATUSES: tuple[str, ...] = (NOT_STARTED, IN_PROGRESS, COMPLETED)


class Progress:
    """Прогресс пользователя в игре.

    Процент, статус, шкала и оставшееся время - вычисляемые свойства:
    они не хранятся, а рассчитываются по сыгранным часам и времени
    прохождения игры.
    """

    def __init__(self, user: User, game: Game, hours: float) -> None:
        """Создать прогресс пользователя в игре по сыгранным часам."""
        if hours < 0:
            raise ValueError("Сыгранное время не может быть отрицательным.")
        self.user = user
        self.game = game
        self.hours = float(hours)

    def __str__(self) -> str:
        """Вернуть шкалу, процент и статус прохождения."""
        return f"[{self.progress_bar}] {self.percent:.0f}% - {self.status}"

    @property
    def percent(self) -> float:
        """Процент прохождения, не больше 100.

        Свойство развивает функцию calculate_progress() сценария ПР1.
        """
        percent = self.hours / self.game.hours_total * FULL_PROGRESS
        return min(percent, FULL_PROGRESS)

    @property
    def hours_left(self) -> float:
        """Сколько часов осталось до примерного времени прохождения."""
        return max(self.game.hours_total - self.hours, 0.0)

    @property
    def status(self) -> str:
        """Статус прохождения: не начата, в процессе или пройдена.

        Свойство развивает функцию get_status() сценария ПР1.
        """
        if self.hours == 0:
            return NOT_STARTED
        if self.percent >= FULL_PROGRESS:
            return COMPLETED
        return IN_PROGRESS

    @property
    def progress_bar(self) -> str:
        """Текстовая шкала прогресса.

        Свойство развивает функцию make_progress_bar() сценария ПР1.
        """
        filled = int(self.percent // PROGRESS_BAR_LENGTH)
        return "#" * filled + "-" * (PROGRESS_BAR_LENGTH - filled)
