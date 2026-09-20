"""Тесты сохранения и загрузки данных проекта в JSON-файлах."""

import os
from datetime import date

import pytest

from games import add_game
from sessions import log_session
from stats import library_stats
from storage import (
    load_games,
    load_sessions,
    save_games,
    save_sessions,
)


def test_games_survive_save_and_load(tmp_path):
    filename = os.path.join(tmp_path, "games.json")
    games: dict[int, dict] = {}
    add_game(games, "Celeste", "Платформер", "PC", 2018, 12.0, 9)
    save_games(games, filename)
    assert load_games(filename) == games


def test_sessions_survive_save_and_load(tmp_path):
    filename = os.path.join(tmp_path, "sessions.json")
    sessions: list[dict] = []
    log_session(sessions, 1, date(2026, 9, 15), 2.5)
    save_sessions(sessions, filename)
    assert load_sessions(filename) == sessions


def test_missing_file_gives_empty_library(tmp_path):
    filename = os.path.join(tmp_path, "нет-такого-файла.json")
    assert load_games(filename) == {}


def test_broken_json_raises_value_error(tmp_path):
    filename = os.path.join(tmp_path, "games.json")
    with open(filename, "w", encoding="utf-8") as file:
        file.write("{не json")
    with pytest.raises(ValueError):
        load_games(filename)


def test_library_stats():
    games: dict[int, dict] = {}
    game_id = add_game(games, "Celeste", "Платформер", "PC", 2018, 12.0, 8)
    sessions: list[dict] = []
    log_session(sessions, game_id, date(2026, 9, 15), 12.0)
    report = library_stats(games, sessions)
    assert report["games"] == 1
    assert report["hours"] == 12.0
    assert report["statuses"]["Пройдена"] == 1
