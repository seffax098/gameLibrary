"""Сохранение и загрузка данных проекта в JSON-файлах.

Чтение и запись выполняются через контекстный менеджер ``with``.
Ошибки файлов и разбора JSON преобразуются в исключение ValueError
с понятным сообщением.
"""

import json
import os
from datetime import date

DATA_DIR: str = "data"
GAMES_FILE: str = os.path.join(DATA_DIR, "games.json")
SESSIONS_FILE: str = os.path.join(DATA_DIR, "sessions.json")


def _read_json(filename: str) -> list:
    """Прочитать список записей из JSON-файла.

    Отсутствие файла считается пустой коллекцией: при первом запуске
    программы данных ещё нет.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Файл {filename} повреждён: {error.msg}."
        ) from error
    except OSError as error:
        raise ValueError(
            f"Не удалось прочитать файл {filename}: {error.strerror}."
        ) from error
    if not isinstance(data, list):
        raise ValueError(f"Файл {filename} должен содержать список.")
    return data


def _write_json(filename: str, records: list) -> None:
    """Записать список записей в JSON-файл."""
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
    except OSError as error:
        raise ValueError(
            f"Не удалось записать файл {filename}: {error.strerror}."
        ) from error


def load_games(filename: str = GAMES_FILE) -> dict[int, dict]:
    """Загрузить игры из JSON-файла в словарь games."""
    games: dict[int, dict] = {}
    for record in _read_json(filename):
        try:
            game_id = int(record["id"])
            games[game_id] = {
                "title": record["title"],
                "genre": record["genre"],
                "platform": record["platform"],
                "release_year": int(record["release_year"]),
                "hours_total": float(record["hours_total"]),
                "rating": int(record.get("rating", 0)),
            }
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Некорректная запись игры в файле {filename}: {error}."
            ) from error
    return games


def save_games(
    games: dict[int, dict],
    filename: str = GAMES_FILE,
) -> None:
    """Сохранить игры в JSON-файл."""
    records = [
        {"id": game_id, **game} for game_id, game in sorted(games.items())
    ]
    _write_json(filename, records)


def load_sessions(filename: str = SESSIONS_FILE) -> list[dict]:
    """Загрузить игровые сессии из JSON-файла."""
    loaded: list[dict] = []
    for record in _read_json(filename):
        try:
            loaded.append({
                "id": int(record["id"]),
                "game_id": int(record["game_id"]),
                "date": date.fromisoformat(record["date"]),
                "hours": float(record["hours"]),
            })
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Некорректная запись сессии в файле {filename}: "
                f"{error}."
            ) from error
    return loaded


def save_sessions(
    sessions: list[dict],
    filename: str = SESSIONS_FILE,
) -> None:
    """Сохранить игровые сессии в JSON-файл."""
    records = [
        {
            "id": session["id"],
            "game_id": session["game_id"],
            "date": session["date"].isoformat(),
            "hours": session["hours"],
        }
        for session in sessions
    ]
    _write_json(filename, records)
