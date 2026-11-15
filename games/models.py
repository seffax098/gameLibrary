"""Django-модели приложения игр."""

from datetime import date
from uuid import uuid4

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode

from models.games import FIRST_GAME_YEAR, MAX_RATING, PLATFORMS
from models.games import Game as LibraryGame


LONG_GAME_HOURS = 50
GAME_SLUG_MAX_LENGTH = 180


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
    is_long = models.GeneratedField(
        expression=models.Case(
            models.When(hours_total__gte=LONG_GAME_HOURS, then=True),
            default=False,
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="длительная игра",
    )
    slug = models.SlugField(
        "URL-идентификатор", max_length=GAME_SLUG_MAX_LENGTH,
        unique=True, editable=False,
    )
    rating = models.PositiveSmallIntegerField(
        "оценка", null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_RATING)],
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Названия в админке и ограничения данных игры."""

        verbose_name = "игра"
        verbose_name_plural = "Игры"
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

    def save(self, *args, **kwargs) -> None:
        """Назначить новой игре постоянный адрес перед сохранением."""
        if not self.slug:
            suffix = uuid4().hex
            limit = GAME_SLUG_MAX_LENGTH - len(suffix) - 1
            title_slug = slugify(unidecode(self.title))[:limit].rstrip("-_")
            self.slug = f"{title_slug or 'game'}-{suffix}"
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Вернуть адрес карточки игры по её слагу."""
        return reverse("games:detail", kwargs={"slug": self.slug})

    def as_library_game(self) -> LibraryGame:
        """Вернуть игру для существующих расчётов и описаний."""
        return LibraryGame(
            self.pk, self.title, self.genre, self.platform,
            self.release_year, self.hours_total, self.rating or 0,
        )
