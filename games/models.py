"""Django-модели приложения игр."""

from datetime import date

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from models.games import FIRST_GAME_YEAR, MAX_RATING, PLATFORMS
from models.games import Game as LibraryGame


def current_year() -> int:
    """Вернуть текущий год для проверки года выпуска."""
    return date.today().year


class Game(models.Model):
    """Игра из каталога библиотеки."""

    objects = models.Manager["Game"]()
    title = models.CharField("название", max_length=255)
    genre = models.CharField("жанр", max_length=100, default="Не указан")
    platform = models.CharField(
        "платформа", max_length=32, choices=[(p, p) for p in PLATFORMS]
    )
    release_year = models.PositiveSmallIntegerField(
        "год выпуска",
        validators=[
            MinValueValidator(FIRST_GAME_YEAR),
            MaxValueValidator(current_year),
        ],
    )
    hours_total = models.FloatField("время прохождения")
    rating = models.PositiveSmallIntegerField(
        "оценка", null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_RATING)],
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Ограничения времени прохождения и оценки."""

        constraints = [
            models.CheckConstraint(
                condition=models.Q(hours_total__gt=0),
                name="game_positive_hours",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__isnull=True) | models.Q(
                    rating__range=(1, MAX_RATING)
                ),
                name="game_rating_range",
            ),
        ]

    def __str__(self) -> str:
        return str(self.title)

    def as_library_game(self) -> LibraryGame:
        """Вернуть игру для существующих расчётов и описаний."""
        return LibraryGame(
            self.pk, self.title, self.genre, self.platform,
            self.release_year, self.hours_total, self.rating or 0,
        )
