"""Игры библиотеки и функции работы с коллекцией игр.

Игра описывается классом ``Game``, библиотека хранится в списке
объектов ``Game``. Проверка данных, возраст игры и описание оценки
относятся к конкретной игре и реализованы методами класса; поиск,
отбор и сортировка работают с коллекцией и остались функциями.
"""

from collections.abc import Callable
from datetime import date
from typing import Any

PLATFORMS: tuple[str, ...] = (
    "PC",
    "PlayStation",
    "Xbox",
    "Nintendo Switch",
)

FIRST_GAME_YEAR: int = 1958
NEW_GAME_AGE: int = 1
CLASSIC_GAME_AGE: int = 15
MAX_RATING: int = 10
SORT_KEYS: tuple[str, ...] = ("title", "year", "rating", "hours")


class Game:
    """Игра в библиотеке."""

    def __init__(
        self,
        game_id: int,
        title: str,
        genre: str,
        platform: str,
        release_year: int,
        hours_total: float,
        rating: int = 0,
    ) -> None:
        """Создать игру, проверив её данные.

        При некорректных значениях возбуждается исключение ValueError,
        поэтому объект Game всегда содержит допустимые данные.
        """
        title = title.strip()
        if not title:
            raise ValueError("Название игры не может быть пустым.")
        if not Game.validate_platform(platform):
            raise ValueError(f"Неизвестная платформа: {platform}.")
        if not Game.validate_year(release_year):
            raise ValueError(
                f"Год выпуска должен быть от {FIRST_GAME_YEAR} "
                f"до {date.today().year}."
            )
        if hours_total <= 0:
            raise ValueError("Время прохождения должно быть больше нуля.")
        if not Game.validate_rating(rating):
            raise ValueError(f"Оценка должна быть от 0 до {MAX_RATING}.")
        self.id = game_id
        self.title = title
        self.genre = genre.strip() or "Не указан"
        self.platform = platform
        self.release_year = release_year
        self.hours_total = float(hours_total)
        self.rating = rating

    def __str__(self) -> str:
        """Вернуть строковое представление игры."""
        return f"{self.title} ({self.platform}, {self.release_year})"

    @staticmethod
    def validate_platform(platform: str) -> bool:
        """Проверить, что платформа входит в список поддерживаемых."""
        return platform in PLATFORMS

    @staticmethod
    def validate_year(release_year: int) -> bool:
        """Проверить, что год выпуска не раньше первой игры и не в будущем."""
        return FIRST_GAME_YEAR <= release_year <= date.today().year

    @staticmethod
    def validate_rating(rating: int) -> bool:
        """Проверить, что оценка лежит в допустимых границах."""
        return 0 <= rating <= MAX_RATING

    @classmethod
    def from_data(cls, data: dict) -> "Game":
        """Создать игру из набора данных, прочитанного из JSON."""
        return cls(
            int(data["id"]),
            data["title"],
            data["genre"],
            data["platform"],
            int(data["release_year"]),
            float(data["hours_total"]),
            int(data.get("rating", 0)),
        )

    def to_data(self) -> dict:
        """Вернуть данные игры для сохранения в JSON."""
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "platform": self.platform,
            "release_year": self.release_year,
            "hours_total": self.hours_total,
            "rating": self.rating,
        }

    def matches(self, query: str) -> bool:
        """Проверить, содержат ли название или жанр игры подстроку."""
        query = query.strip().lower()
        return query in f"{self.title} {self.genre}".lower()

    def is_released_since(self, year: int) -> bool:
        """Проверить, что игра выпущена не раньше указанного года."""
        return self.release_year >= year

    def age(self, current_year: int | None = None) -> int:
        """Вернуть возраст игры в годах."""
        if current_year is None:
            current_year = date.today().year
        return current_year - self.release_year

    def era(self, current_year: int | None = None) -> str:
        """Вернуть словесную характеристику возраста игры.

        Метод развивает функцию get_era() первоначального сценария ПР1.
        """
        game_age = self.age(current_year)
        if game_age <= NEW_GAME_AGE:
            return "новинка"
        if game_age >= CLASSIC_GAME_AGE:
            return "классика"
        return "современная игра"

    def rating_label(self) -> str:
        """Вернуть текстовое описание оценки игры.

        Метод развивает функцию get_rating_label() сценария ПР1.
        """
        if not self.rating:
            return "не выставлена"
        if self.rating >= 9:
            return f"{self.rating}/10 - шедевр"
        if self.rating >= 7:
            return f"{self.rating}/10 - хорошая игра"
        if self.rating >= 5:
            return f"{self.rating}/10 - средняя игра"
        return f"{self.rating}/10 - разочарование"


def next_game_id(games: list[Game]) -> int:
    """Вернуть свободный идентификатор для новой игры."""
    if not games:
        return 1
    return max(game.id for game in games) + 1


def add_game(
    games: list[Game],
    title: str,
    genre: str,
    platform: str,
    release_year: int,
    hours_total: float,
    rating: int = 0,
) -> Game:
    """Создать игру, добавить её в библиотеку и вернуть созданный объект.

    Проверку данных выполняет конструктор Game: при некорректных
    значениях возбуждается исключение ValueError.
    """
    game = Game(
        next_game_id(games),
        title,
        genre,
        platform,
        release_year,
        hours_total,
        rating,
    )
    games.append(game)
    return game


def find_game_by_id(games: list[Game], game_id: int) -> Game | None:
    """Найти игру по идентификатору.

    Если игры нет, возвращается None: веб-страница игры проверяет
    результат и отвечает кодом 404.
    """
    for game in games:
        if game.id == game_id:
            return game
    return None


def get_game(games: list[Game], game_id: int) -> Game:
    """Вернуть игру по идентификатору.

    Если игра не найдена, возбуждается исключение KeyError.
    """
    game = find_game_by_id(games, game_id)
    if game is None:
        raise KeyError(f"Игра с идентификатором {game_id} не найдена.")
    return game


def remove_game(games: list[Game], game_id: int) -> Game:
    """Удалить игру из библиотеки и вернуть удалённый объект.

    Если игра не найдена, возбуждается исключение KeyError.
    """
    game = get_game(games, game_id)
    games.remove(game)
    return game


def find_games(games: list[Game], query: str) -> list[Game]:
    """Найти игры по подстроке названия или жанра без учёта регистра."""
    return [game for game in games if game.matches(query)]


def filter_games_by_platform(games: list[Game], platform: str) -> list[Game]:
    """Отобрать игры выбранной платформы."""
    return [game for game in games if game.platform == platform]


def filter_games_by_year(games: list[Game], min_year: int) -> list[Game]:
    """Отобрать игры, выпущенные не раньше указанного года."""
    return [game for game in games if game.is_released_since(min_year)]


def sort_games(games: list[Game], sort_key: str = "title") -> list[Game]:
    """Вернуть новый список игр, отсортированный по выбранному ключу.

    Ключ сортировки задаётся lambda-функцией: по названию, году
    выпуска, оценке или времени прохождения.
    """
    if sort_key not in SORT_KEYS:
        raise ValueError(f"Неизвестный ключ сортировки: {sort_key}.")
    keys: dict[str, Callable[[Game], Any]] = {
        "title": lambda game: game.title.lower(),
        "year": lambda game: -game.release_year,
        "rating": lambda game: -game.rating,
        "hours": lambda game: game.hours_total,
    }
    return sorted(games, key=keys[sort_key])


def get_platforms(games: list[Game]) -> set[str]:
    """Вернуть множество платформ, представленных в библиотеке."""
    return {game.platform for game in games}
