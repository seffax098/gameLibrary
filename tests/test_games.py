"""Тесты класса Game и функций работы с коллекцией игр."""

import pytest

from models import Game
from models.games import (
    add_game,
    filter_games_by_platform,
    filter_games_by_year,
    find_games,
    get_game,
    remove_game,
    sort_games,
)


def make_library() -> list[Game]:
    """Подготовить библиотеку из двух игр для тестов."""
    games: list[Game] = []
    add_game(games, "The Witcher 3", "RPG", "PC", 2015, 100.0, 10)
    add_game(games, "Hades", "Roguelike", "Nintendo Switch", 2020, 40.0, 9)
    return games


def test_game_creation() -> None:
    """Конструктор сохраняет данные в атрибутах объекта."""
    game = Game(1, "Hollow Knight", "Метроидвания", "PC", 2017, 35, 9)
    assert game.id == 1
    assert game.title == "Hollow Knight"
    assert game.genre == "Метроидвания"
    assert game.platform == "PC"
    assert game.release_year == 2017
    assert game.hours_total == 35.0
    assert game.rating == 9


def test_game_str() -> None:
    """Строковое представление содержит название, платформу и год."""
    game = Game(1, "Hades", "Roguelike", "Nintendo Switch", 2020, 40.0)
    assert str(game) == "Hades (Nintendo Switch, 2020)"


def test_game_empty_genre_is_replaced() -> None:
    """Пустой жанр заменяется на «Не указан»."""
    game = Game(1, "Tetris", "  ", "PC", 1985, 5.0)
    assert game.genre == "Не указан"


@pytest.mark.parametrize(
    "title, platform, year, hours, rating",
    [
        ("  ", "PC", 2017, 35.0, 0),
        ("Halo", "Sega", 2001, 12.0, 0),
        ("Pong", "PC", 1900, 1.0, 0),
        ("Hades", "PC", 2020, 0.0, 0),
        ("Hades", "PC", 2020, 40.0, 11),
    ],
)
def test_game_rejects_invalid_data(
    title: str,
    platform: str,
    year: int,
    hours: float,
    rating: int,
) -> None:
    """Некорректные данные вызывают ValueError в конструкторе."""
    with pytest.raises(ValueError):
        Game(1, title, "Жанр", platform, year, hours, rating)


def test_validate_static_methods() -> None:
    """Статические методы проверяют данные без создания объекта."""
    assert Game.validate_platform("PC")
    assert not Game.validate_platform("Sega")
    assert Game.validate_year(2015)
    assert not Game.validate_year(1900)
    assert Game.validate_rating(0)
    assert not Game.validate_rating(11)


def test_game_matches() -> None:
    """Игра подходит под запрос по названию или жанру."""
    game = Game(1, "The Witcher 3", "RPG", "PC", 2015, 100.0)
    assert game.matches("witch")
    assert game.matches("rpg")
    assert not game.matches("portal")


def test_game_era_and_age() -> None:
    """Возраст игры переводится в словесную эпоху."""
    game = Game(1, "Half-Life", "Шутер", "PC", 2000, 12.0)
    assert game.age(current_year=2026) == 26
    assert game.era(current_year=2026) == "классика"
    assert game.era(current_year=2001) == "новинка"
    assert game.era(current_year=2010) == "современная игра"


def test_game_rating_label() -> None:
    """Оценка переводится в текстовое описание."""
    unrated = Game(1, "Hades", "Roguelike", "PC", 2020, 40.0)
    rated = Game(2, "Celeste", "Платформер", "PC", 2018, 12.0, 10)
    assert unrated.rating_label() == "не выставлена"
    assert rated.rating_label().endswith("шедевр")


def test_game_data_round_trip() -> None:
    """from_data() восстанавливает игру из данных to_data()."""
    game = Game(3, "Celeste", "Платформер", "PC", 2018, 12.0, 9)
    restored = Game.from_data(game.to_data())
    assert isinstance(restored, Game)
    assert restored.to_data() == game.to_data()


def test_add_game() -> None:
    """add_game() создаёт объект Game и добавляет его в коллекцию."""
    games: list[Game] = []
    game = add_game(games, "Hollow Knight", "Метроидвания", "PC",
                    2017, 35.0, 9)
    assert isinstance(game, Game)
    assert games == [game]
    assert add_game(games, "Hades", "Roguelike", "PC", 2020, 40.0).id == 2


def test_add_game_rejects_unknown_platform() -> None:
    """Неизвестная платформа вызывает ValueError, коллекция не меняется."""
    games: list[Game] = []
    with pytest.raises(ValueError):
        add_game(games, "Halo", "Шутер", "Sega", 2001, 12.0)
    assert not games


def test_find_games() -> None:
    """Поиск возвращает список подходящих объектов Game."""
    games = make_library()
    assert [game.title for game in find_games(games, "witcher")] == [
        "The Witcher 3"
    ]
    assert not find_games(games, "portal")


def test_filter_games_by_platform() -> None:
    """Отбор возвращает только игры выбранной платформы."""
    games = make_library()
    selected = filter_games_by_platform(games, "PC")
    assert [game.title for game in selected] == ["The Witcher 3"]


def test_filter_games_by_year() -> None:
    """Отбор по году оставляет игры не старше указанного года."""
    games = make_library()
    selected = filter_games_by_year(games, 2018)
    assert [game.title for game in selected] == ["Hades"]


def test_sort_games() -> None:
    """Игры сортируются по названию и по времени прохождения."""
    games = make_library()
    by_title = [game.title for game in sort_games(games, "title")]
    by_hours = [game.title for game in sort_games(games, "hours")]
    assert by_title == ["Hades", "The Witcher 3"]
    assert by_hours == ["Hades", "The Witcher 3"]
    with pytest.raises(ValueError):
        sort_games(games, "price")


def test_get_game() -> None:
    """Игра находится по идентификатору, иначе KeyError."""
    games = make_library()
    assert get_game(games, 2).title == "Hades"
    with pytest.raises(KeyError):
        get_game(games, 99)


def test_remove_game() -> None:
    """Игра удаляется, повторное удаление вызывает KeyError."""
    games = make_library()
    removed = remove_game(games, 1)
    assert removed.title == "The Witcher 3"
    assert removed not in games
    with pytest.raises(KeyError):
        remove_game(games, 1)
