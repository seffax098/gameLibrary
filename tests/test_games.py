"""Тесты функций работы с играми библиотеки."""

import pytest

from games import (
    add_game,
    filter_games_by_platform,
    find_games,
    get_era,
    get_rating_label,
    remove_game,
    sort_games,
)


def make_library() -> dict[int, dict]:
    """Подготовить библиотеку из двух игр для тестов."""
    games: dict[int, dict] = {}
    add_game(games, "The Witcher 3", "RPG", "PC", 2015, 100.0, 10)
    add_game(games, "Hades", "Roguelike", "Nintendo Switch", 2020, 40.0, 9)
    return games


def test_add_game() -> None:
    games: dict[int, dict] = {}
    game_id = add_game(games, "Hollow Knight", "Метроидвания", "PC",
                       2017, 35.0, 9)
    assert len(games) == 1
    assert games[game_id]["title"] == "Hollow Knight"
    assert games[game_id]["platform"] == "PC"


def test_add_game_rejects_unknown_platform() -> None:
    games: dict[int, dict] = {}
    with pytest.raises(ValueError):
        add_game(games, "Halo", "Шутер", "Sega", 2001, 12.0)


def test_find_games() -> None:
    games = make_library()
    assert find_games(games, "witcher")
    assert not find_games(games, "portal")


def test_filter_games_by_platform() -> None:
    games = make_library()
    selected = filter_games_by_platform(games, "PC")
    assert len(selected) == 1


def test_sort_games_by_title() -> None:
    games = make_library()
    titles = [game["title"] for _, game in sort_games(games, "title")]
    assert titles == ["Hades", "The Witcher 3"]


def test_remove_game() -> None:
    games = make_library()
    remove_game(games, 1)
    assert 1 not in games
    with pytest.raises(KeyError):
        remove_game(games, 1)


def test_get_era() -> None:
    assert get_era(2000, current_year=2026) == "классика"
    assert get_era(2026, current_year=2026) == "новинка"


def test_get_rating_label() -> None:
    assert get_rating_label(0) == "не выставлена"
    assert get_rating_label(10).endswith("шедевр")
