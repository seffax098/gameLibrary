-- ==========================================
-- Игровая библиотека: структура базы данных
-- ==========================================
--
-- games    - игры библиотеки;
-- users    - игроки;
-- sessions - игровые сессии: кто, во что, когда и сколько играл.
--
-- Связи: sessions.user_id -> users.id, sessions.game_id -> games.id.
-- Повторный запуск безопасен: IF NOT EXISTS не пересоздаёт таблицы.

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    platform TEXT NOT NULL,
    release_year INTEGER NOT NULL,
    hours_total REAL NOT NULL,
    -- NULL - оценка не выставлена (в JSON это значение 0).
    rating INTEGER
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    -- Почта пользователя уникальна.
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    -- Дата в формате YYYY-MM-DD: строки сравниваются и сортируются
    -- в хронологическом порядке.
    session_date TEXT NOT NULL,
    hours REAL NOT NULL,
    -- 0 - сессия активна, 1 - отменена.
    is_cancelled INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id)
);
