"""Сохранение и загрузка данных проекта в JSON-файлах.

JSON остаётся форматом хранения, а приложение работает с объектами:
при загрузке записи файлов превращаются в объекты Game, User и
GameSession, при сохранении объекты превращаются обратно в записи.
Связи сессии с пользователем и игрой хранятся в файле идентификаторами
user_id и game_id и при загрузке восстанавливаются в ссылки на объекты.

Чтение и запись выполняются через контекстный менеджер ``with``.
Ошибки файлов и разбора JSON преобразуются в исключение ValueError
с понятным сообщением.
"""

import json
import os
from collections.abc import Callable
from typing import TypeVar

from models import Game, GameSession, User
from models.games import get_game
from models.users import get_user

DATA_DIR: str = "data"
GAMES_FILE: str = os.path.join(DATA_DIR, "games.json")
USERS_FILE: str = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE: str = os.path.join(DATA_DIR, "sessions.json")

T = TypeVar("T")


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


def _write_json(filename: str, records: list[dict]) -> None:
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


def _load_objects(
    filename: str,
    kind: str,
    factory: Callable[[dict], T],
) -> list[T]:
    """Прочитать записи JSON-файла и создать по ним объекты.

    Каждая запись передаётся в функцию factory. Если запись
    некорректна, возбуждается ValueError с указанием файла и номера
    записи.
    """
    objects: list[T] = []
    for number, record in enumerate(_read_json(filename), start=1):
        try:
            objects.append(factory(record))
        except KeyError as error:
            raise ValueError(
                f"В записи {kind} №{number} файла {filename} "
                f"нет поля {error}."
            ) from error
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Некорректная запись {kind} №{number} "
                f"в файле {filename}: {error}"
            ) from error
    return objects


def load_games(filename: str = GAMES_FILE) -> list[Game]:
    """Загрузить игры из JSON-файла в список объектов Game."""
    return _load_objects(filename, "игры", Game.from_data)


def save_games(games: list[Game], filename: str = GAMES_FILE) -> None:
    """Сохранить объекты Game в JSON-файл."""
    _write_json(filename, [game.to_data() for game in games])


def load_users(filename: str = USERS_FILE) -> list[User]:
    """Загрузить пользователей из JSON-файла в список объектов User."""
    return _load_objects(filename, "пользователя", User.from_data)


def save_users(users: list[User], filename: str = USERS_FILE) -> None:
    """Сохранить объекты User в JSON-файл."""
    _write_json(filename, [user.to_data() for user in users])


def _session_from_record(
    record: dict,
    users: list[User],
    games: list[Game],
) -> GameSession:
    """Создать сессию из записи JSON, найдя её пользователя и игру.

    В записи хранятся user_id и game_id; по ним в загруженных
    коллекциях находятся объекты User и Game. Если объект не найден,
    сессия не создаётся: возбуждается ValueError.
    """
    user_id = int(record["user_id"])
    game_id = int(record["game_id"])
    try:
        user = get_user(users, user_id)
        game = get_game(games, game_id)
    except KeyError as error:
        raise ValueError(error.args[0]) from error
    return GameSession.from_data(record, user, game)


def load_sessions(
    games: list[Game],
    users: list[User],
    filename: str = SESSIONS_FILE,
) -> list[GameSession]:
    """Загрузить сессии и восстановить их связи с объектами.

    Коллекции games и users должны быть загружены заранее: каждая
    сессия получает ссылки на объекты из этих коллекций.
    """
    return _load_objects(
        filename,
        "сессии",
        lambda record: _session_from_record(record, users, games),
    )


def save_sessions(
    sessions: list[GameSession],
    filename: str = SESSIONS_FILE,
) -> None:
    """Сохранить объекты GameSession в JSON-файл."""
    _write_json(filename, [session.to_data() for session in sessions])
