"""Тесты слоя базы данных: схема, импорт из JSON, запросы проекта."""

import json
import sqlite3
from pathlib import Path

import pytest

from db.database import (
    BASE_DIR,
    create_schema,
    fetch_all,
    fetch_one,
    get_connection,
)
from db.import_json import COUNT_QUERIES, DATA_DIR, import_library

QUERIES_FILE: Path = BASE_DIR / "sql" / "queries.sql"


def split_statements(script: str) -> list[str]:
    """Разделить SQL-файл на отдельные запросы.

    Строки накапливаются, пока sqlite3.complete_statement() не
    подтвердит конец запроса: точка с запятой в комментарии или строке
    запрос не обрывает.
    """
    statements: list[str] = []
    current = ""
    for line in script.splitlines(keepends=True):
        current += line
        if sqlite3.complete_statement(current):
            statements.append(current.strip())
            current = ""
    return statements


def test_schema_creates_tables_and_foreign_keys() -> None:
    """Схема создаёт три таблицы, сессии ссылаются на игры и игроков."""
    conn = get_connection(":memory:")
    create_schema(conn)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    assert tables == [("games",), ("sessions",), ("users",)]
    references = {
        row[2] for row in conn.execute("PRAGMA foreign_key_list(sessions)")
    }
    assert references == {"games", "users"}
    # IF NOT EXISTS: повторное выполнение схемы не вызывает ошибку.
    create_schema(conn)
    conn.close()


def test_foreign_keys_are_checked() -> None:
    """PRAGMA foreign_keys = ON: сессия несуществующей игры не вставится."""
    conn = get_connection(":memory:")
    create_schema(conn)
    conn.execute(
        "INSERT INTO users (id, name, email) VALUES (1, 'A', 'a@a.ru')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO sessions (id, user_id, game_id, session_date, hours)"
            " VALUES (1, 1, 99, '2026-09-10', 1.0)"
        )
    conn.close()


def test_import_matches_json_files(db_path: Path) -> None:
    """Число записей в таблицах совпадает с числом записей в JSON."""
    for table, query in COUNT_QUERIES.items():
        with open(DATA_DIR / f"{table}.json", encoding="utf-8") as file:
            expected = len(json.load(file))
        row = fetch_one(db_path, query)
        assert row is not None and row[0] == expected


def test_import_converts_values(db_path: Path) -> None:
    """Оценка 0 становится NULL, признак отмены - числом 0 или 1."""
    unrated = fetch_all(db_path, "SELECT id FROM games WHERE rating IS NULL")
    assert [row["id"] for row in unrated] == [4]
    flags = fetch_all(
        db_path, "SELECT DISTINCT is_cancelled FROM sessions ORDER BY 1"
    )
    assert [row["is_cancelled"] for row in flags] == [0, 1]


def test_import_can_be_repeated(db_path: Path) -> None:
    """Повторный импорт заменяет данные, а не дублирует их."""
    counts = import_library(db_path, DATA_DIR)
    assert counts == {"games": 4, "users": 2, "sessions": 6}


def test_failed_import_keeps_previous_data(
    db_path: Path,
    tmp_path: Path,
) -> None:
    """При ошибке импорта транзакция откатывается целиком."""
    broken = tmp_path / "broken"
    broken.mkdir()
    for name in ("games.json", "users.json"):
        (broken / name).write_text(
            (DATA_DIR / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (broken / "sessions.json").write_text(
        json.dumps([{
            "id": 1, "user_id": 99, "game_id": 1,
            "date": "2026-09-10", "hours": 1.0, "is_cancelled": False,
        }]),
        encoding="utf-8",
    )
    with pytest.raises(sqlite3.IntegrityError):
        import_library(db_path, broken)
    row = fetch_one(db_path, "SELECT COUNT(*) AS total FROM sessions")
    assert row is not None and row["total"] == 6


def test_rows_are_accessed_by_name(db_path: Path) -> None:
    """fetch_all() и fetch_one() возвращают sqlite3.Row."""
    game = fetch_one(db_path, "SELECT title FROM games WHERE id = ?", [2])
    assert game is not None and game["title"] == "Hades"
    missing = fetch_one(db_path, "SELECT id FROM games WHERE id = ?", [99])
    assert missing is None


def test_missing_database_is_not_created(tmp_path: Path) -> None:
    """Отсутствующая база не создаётся пустой: ошибка с подсказкой."""
    path = tmp_path / "missing.sqlite"
    with pytest.raises(FileNotFoundError, match="db.import_json"):
        fetch_all(path, "SELECT 1")
    assert not path.exists()


def test_project_queries_run(db_path: Path) -> None:
    """Все запросы sql/queries.sql выполняются на данных проекта."""
    statements = split_statements(QUERIES_FILE.read_text(encoding="utf-8"))
    assert len(statements) >= 10
    conn = get_connection(db_path)
    for statement in statements:
        conn.execute(statement).fetchall()
    conn.close()


def test_unplayed_games_query(db_path: Path) -> None:
    """Подзапрос NOT IN исключает только игры с активными сессиями."""
    query = """
        SELECT title FROM games
        WHERE id NOT IN (
            SELECT game_id FROM sessions
            WHERE user_id = ? AND is_cancelled = 0
        )
        ORDER BY title
    """
    anna = [row["title"] for row in fetch_all(db_path, query, [2])]
    assert anna == ["God of War", "Hades"]
