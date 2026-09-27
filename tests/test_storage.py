"""Тесты сохранения и загрузки объектов в JSON-файлах."""

import json
import os
from datetime import date
from pathlib import Path

import pytest

from models import Game, GameSession, User
from models.games import add_game
from models.sessions import log_session
from storage import (
    load_games,
    load_sessions,
    load_users,
    save_games,
    save_sessions,
    save_users,
)

DAY: date = date(2026, 9, 15)


def test_games_survive_save_and_load(tmp_path: Path) -> None:
    """Игры сохраняются в JSON и загружаются как объекты Game."""
    filename = os.path.join(tmp_path, "games.json")
    games: list[Game] = []
    add_game(games, "Celeste", "Платформер", "PC", 2018, 12.0, 9)
    save_games(games, filename)
    loaded = load_games(filename)
    assert all(isinstance(game, Game) for game in loaded)
    assert [game.to_data() for game in loaded] == [
        game.to_data() for game in games
    ]


def test_users_survive_save_and_load(
    tmp_path: Path,
    ivan: User,
    anna: User,
) -> None:
    """Пользователи сохраняются в JSON и загружаются как объекты User."""
    filename = os.path.join(tmp_path, "users.json")
    save_users([ivan, anna], filename)
    loaded = load_users(filename)
    assert all(isinstance(user, User) for user in loaded)
    assert [str(user) for user in loaded] == [str(ivan), str(anna)]


def test_sessions_restore_links_to_objects(
    tmp_path: Path,
    ivan: User,
    anna: User,
    witcher: Game,
) -> None:
    """При загрузке сессия получает ссылки на объекты из коллекций."""
    filename = os.path.join(tmp_path, "sessions.json")
    sessions: list[GameSession] = []
    log_session(sessions, ivan, witcher, DAY, 2.5)
    cancelled = log_session(sessions, anna, witcher, DAY, 1.0)
    assert cancelled is not None
    cancelled.cancel()
    save_sessions(sessions, filename)

    loaded = load_sessions([witcher], [ivan, anna], filename)
    assert loaded[0].user is ivan
    assert loaded[0].game is witcher
    assert loaded[1].user is anna
    assert loaded[1].is_cancelled
    assert [session.to_data() for session in loaded] == [
        session.to_data() for session in sessions
    ]


def test_sessions_file_stores_identifiers(
    tmp_path: Path,
    ivan: User,
    witcher: Game,
) -> None:
    """В JSON вместо объектов хранятся идентификаторы связей."""
    filename = os.path.join(tmp_path, "sessions.json")
    sessions: list[GameSession] = []
    log_session(sessions, ivan, witcher, DAY, 2.5)
    save_sessions(sessions, filename)
    with open(filename, encoding="utf-8") as file:
        records = json.load(file)
    assert records == [
        {
            "id": 1,
            "user_id": 1,
            "game_id": 1,
            "date": "2026-09-15",
            "hours": 2.5,
            "is_cancelled": False,
        }
    ]


def test_session_with_unknown_user_is_rejected(
    tmp_path: Path,
    ivan: User,
    witcher: Game,
) -> None:
    """Сессия без существующего пользователя не загружается."""
    filename = os.path.join(tmp_path, "sessions.json")
    sessions: list[GameSession] = []
    log_session(sessions, ivan, witcher, DAY, 2.5)
    save_sessions(sessions, filename)
    with pytest.raises(ValueError, match="Пользователь"):
        load_sessions([witcher], [], filename)


def test_missing_file_gives_empty_library(tmp_path: Path) -> None:
    """Отсутствующий файл даёт пустую коллекцию."""
    filename = os.path.join(tmp_path, "нет-такого-файла.json")
    assert not load_games(filename)
    assert not load_users(filename)


def test_broken_json_raises_value_error(tmp_path: Path) -> None:
    """Повреждённый JSON вызывает ValueError."""
    filename = os.path.join(tmp_path, "games.json")
    with open(filename, "w", encoding="utf-8") as file:
        file.write("{не json")
    with pytest.raises(ValueError):
        load_games(filename)


@pytest.mark.parametrize(
    "record",
    [
        {"id": 1, "title": "Halo", "genre": "Шутер", "platform": "PC"},
        {
            "id": 1,
            "title": "Halo",
            "genre": "Шутер",
            "platform": "Sega",
            "release_year": 2001,
            "hours_total": 12.0,
        },
    ],
)
def test_invalid_game_record_raises_value_error(
    tmp_path: Path,
    record: dict,
) -> None:
    """Запись без поля или с неверными данными вызывает ValueError."""
    filename = os.path.join(tmp_path, "games.json")
    with open(filename, "w", encoding="utf-8") as file:
        json.dump([record], file)
    with pytest.raises(ValueError, match="№1"):
        load_games(filename)
