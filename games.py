"""Функции для работы с играми библиотеки.

Игры хранятся в словаре ``games``: ключ - числовой идентификатор игры,
значение - словарь с данными игры (название, жанр, платформа, год
выпуска, примерное время прохождения и оценка пользователя).
"""

from datetime import date

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


def next_game_id(games: dict[int, dict]) -> int:
    """Вернуть свободный идентификатор для новой игры."""
    if not games:
        return 1
    return max(games) + 1


def add_game(
    games: dict[int, dict],
    title: str,
    genre: str,
    platform: str,
    release_year: int,
    hours_total: float,
    rating: int = 0,
) -> int:
    """Добавить игру в словарь games и вернуть её идентификатор.

    Данные проверяются перед добавлением: при некорректных значениях
    возбуждается исключение ValueError.
    """
    title = title.strip()
    if not title:
        raise ValueError("Название игры не может быть пустым.")
    if platform not in PLATFORMS:
        raise ValueError(f"Неизвестная платформа: {platform}.")
    current_year = date.today().year
    if not FIRST_GAME_YEAR <= release_year <= current_year:
        raise ValueError(
            f"Год выпуска должен быть от {FIRST_GAME_YEAR} "
            f"до {current_year}."
        )
    if hours_total < 0:
        raise ValueError("Время прохождения не должно быть отрицательным.")
    if not 0 <= rating <= MAX_RATING:
        raise ValueError(f"Оценка должна быть от 0 до {MAX_RATING}.")

    game_id = next_game_id(games)
    games[game_id] = {
        "title": title,
        "genre": genre.strip() or "Не указан",
        "platform": platform,
        "release_year": release_year,
        "hours_total": float(hours_total),
        "rating": rating,
    }
    return game_id


def remove_game(games: dict[int, dict], game_id: int) -> dict:
    """Удалить игру из библиотеки и вернуть её данные.

    Если игра не найдена, возбуждается исключение KeyError.
    """
    if game_id not in games:
        raise KeyError(f"Игра с идентификатором {game_id} не найдена.")
    return games.pop(game_id)


def get_game(games: dict[int, dict], game_id: int) -> dict:
    """Вернуть данные игры по идентификатору."""
    if game_id not in games:
        raise KeyError(f"Игра с идентификатором {game_id} не найдена.")
    return games[game_id]


def find_games(games: dict[int, dict], query: str) -> dict[int, dict]:
    """Найти игры по подстроке названия или жанра.

    Поиск выполняется без учёта регистра, возвращается словарь
    подходящих игр.
    """
    query = query.strip().lower()
    found: dict[int, dict] = {}
    for game_id, game in games.items():
        haystack = f"{game['title']} {game['genre']}".lower()
        if query in haystack:
            found[game_id] = game
    return found


def filter_games_by_platform(
    games: dict[int, dict],
    platform: str,
) -> dict[int, dict]:
    """Отобрать игры выбранной платформы.

    Отбор выполняется генератором пар «идентификатор - игра».
    """
    selected = (
        (game_id, game)
        for game_id, game in games.items()
        if game["platform"] == platform
    )
    return dict(selected)


def filter_games_by_year(
    games: dict[int, dict],
    min_year: int,
) -> dict[int, dict]:
    """Отобрать игры, выпущенные не раньше указанного года."""
    selected = (
        (game_id, game)
        for game_id, game in games.items()
        if game["release_year"] >= min_year
    )
    return dict(selected)


def sort_games(
    games: dict[int, dict],
    sort_key: str = "title",
) -> list[tuple[int, dict]]:
    """Отсортировать игры библиотеки.

    Ключ сортировки задаётся lambda-функцией: по названию, году
    выпуска, оценке или времени прохождения.
    """
    if sort_key not in SORT_KEYS:
        raise ValueError(f"Неизвестный ключ сортировки: {sort_key}.")
    keys = {
        "title": lambda item: item[1]["title"].lower(),
        "year": lambda item: -item[1]["release_year"],
        "rating": lambda item: -item[1]["rating"],
        "hours": lambda item: item[1]["hours_total"],
    }
    return sorted(games.items(), key=keys[sort_key])


def get_platforms(games: dict[int, dict]) -> set[str]:
    """Вернуть множество платформ, представленных в библиотеке."""
    return {game["platform"] for game in games.values()}


def get_game_age(release_year: int, current_year: int | None = None) -> int:
    """Вернуть возраст игры в годах."""
    if current_year is None:
        current_year = date.today().year
    return current_year - release_year


def get_era(release_year: int, current_year: int | None = None) -> str:
    """Вернуть словесную характеристику возраста игры.

    Функция перенесена из первоначального сценария ПР1.
    """
    game_age = get_game_age(release_year, current_year)
    if game_age <= NEW_GAME_AGE:
        return "новинка"
    if game_age >= CLASSIC_GAME_AGE:
        return "классика"
    return "современная игра"


def get_rating_label(rating: int) -> str:
    """Вернуть текстовое описание оценки игры.

    Функция перенесена из первоначального сценария ПР1.
    """
    if not rating:
        return "не выставлена"
    if rating >= 9:
        return f"{rating}/10 - шедевр"
    if rating >= 7:
        return f"{rating}/10 - хорошая игра"
    if rating >= 5:
        return f"{rating}/10 - средняя игра"
    return f"{rating}/10 - разочарование"
