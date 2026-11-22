"""Django-модели приложения игровых сессий."""

from datetime import date

from django.db import models

from models import User


class Player(models.Model):
    """Игрок, для которого ведётся история сессий."""

    objects = models.Manager["Player"]()
    name = models.CharField("имя", max_length=150)
    email = models.EmailField("электронная почта", unique=True)

    class Meta:  # pylint: disable=too-few-public-methods
        """Названия игрока в административной панели."""

        verbose_name = "игрок"
        verbose_name_plural = "Игроки"

    def __str__(self) -> str:
        return str(self.name)

    def as_library_user(self) -> User:
        """Вернуть игрока для расчёта прогресса."""
        return User(self.pk, self.name, self.email)


class GameSessionQuerySet(models.QuerySet["GameSession"]):
    """Повторно используемые выборки из истории сессий."""

    def active(self) -> "GameSessionQuerySet":
        """Выбрать активные сессии."""
        return self.filter(status=GameSession.Status.ACTIVE)

    def cancelled(self) -> "GameSessionQuerySet":
        """Выбрать отменённые сессии."""
        return self.filter(status=GameSession.Status.CANCELLED)

    def completed(self) -> "GameSessionQuerySet":
        """Выбрать завершённые сессии."""
        return self.filter(status=GameSession.Status.COMPLETED)

    def played(self) -> "GameSessionQuerySet":
        """Выбрать сессии, часы которых учитываются в прогрессе."""
        return self.filter(status__in=PLAYED_STATUSES)

    def for_date(self, session_date: date) -> "GameSessionQuerySet":
        """Выбрать сессии за указанную дату."""
        return self.filter(session_date=session_date)


class GameSession(models.Model):
    """Запись об игре пользователя за конкретный день."""

    # TextChoices наследует стандартные классы Django и Enum.
    # pylint: disable-next=too-many-ancestors
    class Status(models.TextChoices):
        """Состояние записи в истории сессий."""

        ACTIVE = "active", "активна"
        CANCELLED = "cancelled", "отменена"
        COMPLETED = "completed", "завершена"

    objects = GameSessionQuerySet.as_manager()
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="sessions",
        verbose_name="игрок",
    )
    game = models.ForeignKey(
        "games.Game", on_delete=models.CASCADE, related_name="sessions",
        verbose_name="игра",
    )
    session_date = models.DateField("дата")
    hours = models.FloatField("сыграно часов")
    status = models.CharField(
        "статус", max_length=9, choices=Status.choices, default=Status.ACTIVE,
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Названия в админке и ограничения данных сессии."""

        verbose_name = "игровая сессия"
        verbose_name_plural = "Игровые сессии"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hours__gt=0),
                name="session_positive_hours",
            ),
            models.UniqueConstraint(
                fields=["player", "game", "session_date"],
                condition=models.Q(status="active"),
                name="unique_active_session_per_day",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=("active", "cancelled", "completed")
                ),
                name="game_session_valid_status",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.player} — {self.game}, {self.session_date:%d.%m.%Y}"

    def cancel(self) -> bool:
        """Перевести активную сессию в отменённые."""
        updated = self.__class__.objects.active().filter(pk=self.pk).update(
            status=self.Status.CANCELLED
        )
        if updated:
            self.status = self.Status.CANCELLED
        return bool(updated)


PLAYED_STATUSES = (GameSession.Status.ACTIVE, GameSession.Status.COMPLETED)
