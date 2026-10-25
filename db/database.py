"""Подключение к базе данных SQLite игровой библиотеки.

Модуль не зависит от Django: его использует и скрипт импорта
db/import_json.py, и view-функции. Путь к базе по умолчанию -
data/gamelibrary.sqlite, view-функции передают путь из настройки
LIBRARY_DB, чтобы тесты могли подменить базу.
"""

import os
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "gamelibrary.sqlite"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"

DbPath = str | os.PathLike[str]


def get_connection(db_path: DbPath = DB_PATH) -> sqlite3.Connection:
    """Открыть соединение и включить проверку внешних ключей.

    По умолчанию SQLite не проверяет, что внешний ключ ссылается на
    существующую запись, поэтому PRAGMA выполняется при каждом
    подключении.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Создать таблицы командами из файла sql/schema.sql."""
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _open_for_reading(db_path: DbPath) -> sqlite3.Connection:
    """Открыть существующую базу; строки результата - sqlite3.Row.

    sqlite3.connect() создал бы пустой файл на месте отсутствующей
    базы, и страница упала бы с ошибкой «no such table». Поэтому
    наличие файла проверяется заранее.
    """
    if db_path != ":memory:" and not os.path.exists(db_path):
        raise FileNotFoundError(
            f"База данных {db_path} не найдена. "
            "Создайте её командой: python -m db.import_json"
        )
    conn = get_connection(db_path)
    # Доступ к полям по имени: row["title"] в Python,
    # {{ game.title }} в шаблоне.
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(
    db_path: DbPath,
    query: str,
    params: list[Any] | tuple[Any, ...] = (),
) -> list[sqlite3.Row]:
    """Выполнить SELECT и вернуть все строки результата.

    Значения передаются отдельно от текста запроса через параметры ?.
    """
    conn = _open_for_reading(db_path)
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def fetch_one(
    db_path: DbPath,
    query: str,
    params: list[Any] | tuple[Any, ...] = (),
) -> sqlite3.Row | None:
    """Выполнить SELECT и вернуть первую строку или None."""
    conn = _open_for_reading(db_path)
    try:
        row: sqlite3.Row | None = conn.execute(query, params).fetchone()
        return row
    finally:
        conn.close()
