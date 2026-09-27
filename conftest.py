"""Настройка pytest: корень проекта доступен для импорта модулей.

Здесь же определены общие объекты для тестов: пользователи и игры.
"""

import pytest

from models import Game, User


@pytest.fixture
def ivan() -> User:
    """Пользователь Иван Петров."""
    return User(1, "Иван Петров", "ivan@example.com")


@pytest.fixture
def anna() -> User:
    """Пользователь Анна Смирнова."""
    return User(2, "Анна Смирнова", "anna@example.com")


@pytest.fixture
def witcher() -> Game:
    """Игра с примерным временем прохождения 100 часов."""
    return Game(1, "The Witcher 3", "RPG", "PC", 2015, 100.0, 10)


@pytest.fixture
def celeste() -> Game:
    """Игра с примерным временем прохождения 12 часов."""
    return Game(2, "Celeste", "Платформер", "PC", 2018, 12.0, 8)
