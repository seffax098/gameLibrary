"""Общие тестовые данные для проверки страниц Django-приложений.

Страницы проверяются на временном каталоге данных, а не на каталоге
data/ проекта: так тесты не зависят от содержимого рабочих JSON-файлов.
Данные создаются и сохраняются функциями ПР3.
"""

import os
import shutil
import tempfile
from datetime import date

from django.test import SimpleTestCase, override_settings

from models import Game, GameSession, User
from models.games import add_game
from models.sessions import log_session
from models.users import add_user
from storage import save_games, save_sessions, save_users


class LibraryTestCase(SimpleTestCase):
    """Базовый класс тестов страниц с тестовой библиотекой.

    Подменяет DATA_DIR временным каталогом. Библиотека: две игры (у
    второй название с HTML-символами), два игрока, активная сессия Ивана
    и отменённая сессия Анны в The Witcher 3.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Создать JSON-файлы и включить подмену настроек."""
        data_dir = tempfile.mkdtemp()
        cls.addClassCleanup(shutil.rmtree, data_dir)

        games: list[Game] = []
        users: list[User] = []
        sessions: list[GameSession] = []
        witcher = add_game(
            games, "The Witcher 3", "RPG", "PC", 2015, 100.0, 10
        )
        add_game(games, "Tom & Jerry <Classic>", "", "PC", 2001, 5.0)
        ivan = add_user(users, "Иван Петров", "ivan@example.com")
        anna = add_user(users, "Анна Смирнова", "anna@example.com")
        log_session(sessions, ivan, witcher, date(2026, 9, 10), 4.5)
        cancelled = log_session(sessions, anna, witcher, date(2026, 9, 11), 2)
        assert cancelled is not None
        cancelled.cancel()

        save_games(games, os.path.join(data_dir, "games.json"))
        save_users(users, os.path.join(data_dir, "users.json"))
        save_sessions(sessions, os.path.join(data_dir, "sessions.json"))

        data_settings = override_settings(DATA_DIR=data_dir)
        data_settings.enable()
        cls.addClassCleanup(data_settings.disable)
        super().setUpClass()
