"""Объектная модель игровой библиотеки.

Пакет содержит классы предметной области и функции работы с их
коллекциями: Game - игра, User - пользователь, GameSession - игровая
сессия пользователя по игре, Progress - прогресс прохождения игры
пользователем.
"""

from .games import Game
from .progress import Progress
from .sessions import GameSession
from .users import User

__all__ = ["Game", "GameSession", "Progress", "User"]
