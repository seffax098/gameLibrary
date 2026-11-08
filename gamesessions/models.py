"""Django-модели приложения игровых сессий."""

from django.db import models

from models import User


class Player(models.Model):
    """Игрок, для которого ведётся история сессий."""

    objects = models.Manager["Player"]()
    name = models.CharField("имя", max_length=150)
    email = models.EmailField("электронная почта", unique=True)

    def __str__(self) -> str:
        return str(self.name)

    def as_library_user(self) -> User:
        """Вернуть игрока для расчёта прогресса."""
        return User(self.pk, self.name, self.email)


class GameSession(models.Model):
    """Запись об игре пользователя за конкретный день."""

    objects = models.Manager["GameSession"]()
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="sessions"
    )
    game = models.ForeignKey(
        "games.Game", on_delete=models.CASCADE, related_name="sessions"
    )
    session_date = models.DateField("дата")
    hours = models.FloatField("сыграно часов")
    is_cancelled = models.BooleanField("отменена", default=False)

    class Meta:  # pylint: disable=too-few-public-methods
        """Ограничения часов и числа активных сессий за день."""

        constraints = [
            models.CheckConstraint(
                condition=models.Q(hours__gt=0),
                name="session_positive_hours",
            ),
            models.UniqueConstraint(
                fields=["player", "game", "session_date"],
                condition=models.Q(is_cancelled=False),
                name="unique_active_session_per_day",
            ),
        ]

    def __str__(self) -> str:
        return f"Сессия №{self.pk} ({self.session_date})"
