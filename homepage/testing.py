"""Тестовые данные для страниц библиотеки."""

from datetime import date

from django.test import TestCase

from games.models import Game
from gamesessions.models import GameSession, Player


class LibraryTestCase(TestCase):
    """Страницы работают с моделями в тестовой базе Django."""

    @classmethod
    def setUpTestData(cls) -> None:
        Game.objects.create(
            pk=1, title="The Witcher 3", genre="RPG", platform="PC",
            release_year=2015, hours_total=100, rating=10,
        )
        Game.objects.create(
            pk=2, title="Tom & Jerry <Classic>", platform="PC",
            release_year=2001, hours_total=5,
        )
        Player.objects.create(
            pk=1, name="Иван Петров", email="ivan@example.com"
        )
        Player.objects.create(
            pk=2, name="Анна Смирнова", email="anna@example.com"
        )
        GameSession.objects.create(
            pk=1, player_id=1, game_id=1,
            session_date=date(2026, 9, 10), hours=4.5,
        )
        GameSession.objects.create(
            pk=2, player_id=2, game_id=1,
            session_date=date(2026, 9, 11), hours=2, is_cancelled=True,
        )
