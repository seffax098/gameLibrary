"""Перенос данных игровой библиотеки из JSON-файлов в SQLite.

Запуск из корня проекта: python -m db.import_json

Скрипт создаёт таблицы (sql/schema.sql), очищает их и заново
переносит игры, пользователей и сессии. Поэтому его можно запускать
повторно: база всегда соответствует текущим JSON-файлам. Весь перенос
выполняется в одной транзакции - при ошибке база остаётся прежней.

Порядок важен: сессии ссылаются на игры и пользователей внешними
ключами, поэтому сначала переносятся игры и пользователи, а таблица
sessions очищается первой.
"""

import json
import os
import sqlite3
from pathlib import Path

from db.database import DB_PATH, DbPath, create_schema, get_connection

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TABLES: tuple[str, ...] = ("games", "users", "sessions")
# Имя таблицы нельзя передать параметром ?, поэтому запросы подсчёта
# записаны полностью.
COUNT_QUERIES: dict[str, str] = {
    "games": "SELECT COUNT(*) FROM games",
    "users": "SELECT COUNT(*) FROM users",
    "sessions": "SELECT COUNT(*) FROM sessions",
}


def load_json(filename: DbPath) -> list[dict]:
    """Прочитать список записей из JSON-файла."""
    with open(filename, encoding="utf-8") as file:
        records: list[dict] = json.load(file)
    return records


def clear_tables(conn: sqlite3.Connection) -> None:
    """Удалить записи всех таблиц: сначала зависимые сессии."""
    conn.execute("DELETE FROM sessions")
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM games")


def import_games(conn: sqlite3.Connection, games: list[dict]) -> None:
    """Перенести игры; оценка 0 («не выставлена») становится NULL."""
    conn.executemany(
        """
        INSERT INTO games (
            id,
            title,
            genre,
            platform,
            release_year,
            hours_total,
            rating
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                game["id"],
                game["title"],
                game["genre"],
                game["platform"],
                game["release_year"],
                game["hours_total"],
                game.get("rating") or None,
            )
            for game in games
        ],
    )


def import_users(conn: sqlite3.Connection, users: list[dict]) -> None:
    """Перенести пользователей."""
    conn.executemany(
        """
        INSERT INTO users (
            id,
            name,
            email
        )
        VALUES (?, ?, ?)
        """,
        [(user["id"], user["name"], user["email"]) for user in users],
    )


def import_sessions(conn: sqlite3.Connection, sessions: list[dict]) -> None:
    """Перенести сессии; логический признак отмены становится 0 или 1."""
    conn.executemany(
        """
        INSERT INTO sessions (
            id,
            user_id,
            game_id,
            session_date,
            hours,
            is_cancelled
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                session["id"],
                session["user_id"],
                session["game_id"],
                session["date"],
                session["hours"],
                int(session.get("is_cancelled", False)),
            )
            for session in sessions
        ],
    )


def count_rows(conn: sqlite3.Connection) -> dict[str, int]:
    """Подсчитать записи в каждой таблице."""
    return {
        table: conn.execute(query).fetchone()[0]
        for table, query in COUNT_QUERIES.items()
    }


def import_library(
    db_path: DbPath = DB_PATH,
    data_dir: DbPath = DATA_DIR,
) -> dict[str, int]:
    """Создать схему, перенести данные и вернуть число записей таблиц."""
    games = load_json(os.path.join(data_dir, "games.json"))
    users = load_json(os.path.join(data_dir, "users.json"))
    sessions = load_json(os.path.join(data_dir, "sessions.json"))

    conn = get_connection(db_path)
    try:
        create_schema(conn)
        clear_tables(conn)
        import_games(conn, games)
        import_users(conn, users)
        import_sessions(conn, sessions)
        conn.commit()
        return count_rows(conn)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    """Выполнить импорт и сравнить число записей с JSON-файлами."""
    counts = import_library()
    print(f"База данных: {DB_PATH}")
    for table in TABLES:
        in_json = len(load_json(DATA_DIR / f"{table}.json"))
        print(f"{table}: JSON {in_json} -> SQLite {counts[table]}")


if __name__ == "__main__":
    main()
