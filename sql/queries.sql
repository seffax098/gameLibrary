-- ==========================================
-- Игровая библиотека: SQL-запросы проекта
-- ==========================================
--
-- Проверка в SQLite CLI из корня проекта:
--     sqlite3 data/gamelibrary.sqlite
--     sqlite> .headers on
--     sqlite> .mode column
--
-- Значения в условиях (id, даты, пороги) заданы для проверки.
-- В view-функциях на их месте стоит параметр ?, а значение
-- передаётся отдельно: conn.execute(query, [game_id]).
--
-- Виды запросов: [список] - выборка списка объектов, [WHERE] -
-- фильтрация, [JOIN] - соединение таблиц, [агрегат] - агрегатные
-- функции, [GROUP BY] - группировка, [HAVING] - фильтрация групп.


-- ------------------------------------------
-- Игры
-- ------------------------------------------

-- 1. Список игр с часами, сыгранными всеми игроками.
-- [список] [JOIN] [агрегат] [GROUP BY]
-- Страница «Игры» (/games/, games.views.games).
-- LEFT JOIN оставляет игры без сессий: у них played = 0.
SELECT
    games.id,
    games.title,
    games.genre,
    games.platform,
    games.release_year,
    games.hours_total,
    games.rating,
    COALESCE(SUM(sessions.hours), 0) AS played
FROM games
LEFT JOIN sessions
    ON sessions.game_id = games.id
    AND sessions.is_cancelled = 0
GROUP BY games.id
ORDER BY games.id;

-- 2. Карточка игры по идентификатору.
-- [WHERE]
-- Страница игры (/games/1/, games.views.game_detail).
SELECT
    id,
    title,
    genre,
    platform,
    release_year,
    hours_total,
    rating
FROM games
WHERE id = 1;

-- 3. Прогресс каждого игрока в выбранной игре.
-- [JOIN] [агрегат] [GROUP BY]
-- Страница игры (/games/1/): блок «Прогресс игроков».
-- Условие на игру стоит в ON, а не в WHERE: игроки без сессий
-- по этой игре остаются в результате с hours = 0.
SELECT
    users.id,
    users.name,
    users.email,
    COALESCE(SUM(sessions.hours), 0) AS hours
FROM users
LEFT JOIN sessions
    ON sessions.user_id = users.id
    AND sessions.game_id = 1
    AND sessions.is_cancelled = 0
GROUP BY users.id, users.name, users.email
ORDER BY users.id;

-- 4. Активные сессии выбранной игры с именами игроков.
-- [JOIN] [WHERE]
-- Страница игры (/games/1/): блок «Активные сессии».
SELECT
    sessions.id,
    strftime('%d.%m.%Y', sessions.session_date) AS played_on,
    sessions.hours,
    users.name AS user_name
FROM sessions
JOIN users
    ON sessions.user_id = users.id
WHERE sessions.game_id = 1
    AND sessions.is_cancelled = 0
ORDER BY sessions.session_date, sessions.id;

-- 5. Платформы, представленные в библиотеке, без повторов.
-- [список]
-- Страница «Поиск игр» (/games/search/): варианты выпадающего списка.
SELECT DISTINCT platform
FROM games
ORDER BY platform;

-- 6. Поиск игр по платформе, году выпуска и оценке.
-- [WHERE] (несколько условий)
-- Страница «Поиск игр» (/games/search/?platform=PC&year_from=2016).
-- В view: WHERE (? = '' OR platform = ?) - пустая строка означает
-- «любая платформа». COALESCE(rating, 0): игра без оценки (NULL)
-- считается игрой с оценкой 0, иначе сравнение NULL >= 0 исключило
-- бы её из результата.
SELECT
    id,
    title,
    genre,
    platform,
    release_year,
    rating
FROM games
WHERE platform = 'PC'
    AND release_year >= 2016
    AND COALESCE(rating, 0) >= 0
ORDER BY rating DESC, title;

-- 7. Список игроков.
-- [список]
-- Страница «Что поиграть» (/games/unplayed/): выбор игрока.
SELECT
    id,
    name,
    email
FROM users
ORDER BY name;

-- 8. Игры, в которые выбранный игрок ещё не играл.
-- [WHERE] (подзапрос NOT IN)
-- Страница «Что поиграть» (/games/unplayed/?user=1).
-- Подзапрос возвращает игры с активными сессиями игрока, внешний
-- запрос исключает их. Отменённая сессия игру не «занимает».
SELECT
    games.id,
    games.title,
    games.genre,
    games.platform,
    games.hours_total
FROM games
WHERE games.id NOT IN (
    SELECT sessions.game_id
    FROM sessions
    WHERE sessions.user_id = 1
        AND sessions.is_cancelled = 0
)
ORDER BY games.title;


-- ------------------------------------------
-- Игровые сессии
-- ------------------------------------------

-- 9. Все сессии с игроком и игрой, по датам.
-- [список] [JOIN]
-- Страница «Игровые сессии» (/sessions/, gamesessions.views.sessions).
-- Вместо user_id и game_id выводятся имя игрока и название игры.
SELECT
    sessions.id,
    strftime('%d.%m.%Y', sessions.session_date) AS played_on,
    sessions.hours,
    sessions.is_cancelled,
    users.name AS user_name,
    games.id AS game_id,
    games.title AS game_title
FROM sessions
JOIN users
    ON sessions.user_id = users.id
JOIN games
    ON sessions.game_id = games.id
ORDER BY sessions.session_date, sessions.id;

-- 10. Карточка сессии со связанными игроком и игрой.
-- [JOIN] [WHERE]
-- Страница сессии (/sessions/1/, gamesessions.views.session_detail).
-- Псевдонимы AS различают одноимённые поля таблиц: id, name, title.
SELECT
    sessions.id,
    strftime('%d.%m.%Y', sessions.session_date) AS played_on,
    sessions.hours,
    sessions.is_cancelled,
    users.id AS user_id,
    users.name AS user_name,
    users.email AS user_email,
    games.id AS game_id,
    games.title AS game_title,
    games.genre AS game_genre,
    games.platform AS game_platform,
    games.release_year AS game_year,
    games.hours_total AS game_hours_total,
    games.rating AS game_rating
FROM sessions
JOIN users
    ON sessions.user_id = users.id
JOIN games
    ON sessions.game_id = games.id
WHERE sessions.id = 1;

-- 11. Часы игрока в игре по активным сессиям.
-- [агрегат] [WHERE] (несколько условий)
-- Страница сессии (/sessions/1/): блок «Прогресс игрока в игре».
-- Без подходящих записей SUM() возвращает NULL, COALESCE - 0.
SELECT
    COALESCE(SUM(hours), 0) AS hours
FROM sessions
WHERE user_id = 1
    AND game_id = 1
    AND is_cancelled = 0;


-- ------------------------------------------
-- Главная страница
-- ------------------------------------------

-- 12. Сводка библиотеки.
-- [агрегат]
-- Главная (/, homepage.views.index): карточки с показателями.
-- AVG(rating) не учитывает NULL - игры без оценки.
SELECT
    (SELECT COUNT(*) FROM games) AS games_count,
    (SELECT COUNT(*) FROM users) AS users_count,
    (SELECT COUNT(*) FROM sessions WHERE is_cancelled = 0)
        AS sessions_count,
    (SELECT COUNT(*) FROM sessions WHERE is_cancelled = 1)
        AS cancelled_count,
    (SELECT COALESCE(SUM(hours), 0) FROM sessions WHERE is_cancelled = 0)
        AS hours_played,
    (SELECT AVG(rating) FROM games) AS average_rating;

-- 13. Три самые популярные игры по сыгранным часам.
-- [JOIN] [агрегат] [GROUP BY]
-- Главная (/): блок «Популярные игры».
SELECT
    games.id,
    games.title,
    SUM(sessions.hours) AS hours
FROM games
JOIN sessions
    ON sessions.game_id = games.id
WHERE sessions.is_cancelled = 0
GROUP BY games.id, games.title
ORDER BY hours DESC
LIMIT 3;

-- 14. Три самых активных игрока.
-- [JOIN] [агрегат] [GROUP BY]
-- Главная (/): блок «Самые активные игроки».
SELECT
    users.id,
    users.name,
    SUM(sessions.hours) AS hours
FROM users
JOIN sessions
    ON sessions.user_id = users.id
WHERE sessions.is_cancelled = 0
GROUP BY users.id, users.name
ORDER BY hours DESC
LIMIT 3;


-- ------------------------------------------
-- Статистика
-- ------------------------------------------

-- 15. Количество игр и средняя оценка по жанрам.
-- [агрегат] [GROUP BY]
-- Страница «Статистика» (/statistics/, homepage.views.statistics).
SELECT
    genre,
    COUNT(*) AS games_count,
    AVG(rating) AS average_rating
FROM games
GROUP BY genre
ORDER BY games_count DESC, genre;

-- 16. Количество игр и годы выпуска по платформам.
-- [агрегат] [GROUP BY]
-- Страница «Статистика» (/statistics/).
SELECT
    platform,
    COUNT(*) AS games_count,
    MIN(release_year) AS first_year,
    MAX(release_year) AS last_year
FROM games
GROUP BY platform
ORDER BY games_count DESC, platform;

-- 17. Активность игроков: сессии, разные игры, часы.
-- [JOIN] [агрегат] [GROUP BY]
-- Страница «Статистика» (/statistics/).
-- COUNT(sessions.id) не считает NULL: у игрока без сессий будет 0.
SELECT
    users.id,
    users.name,
    COUNT(sessions.id) AS sessions_count,
    COUNT(DISTINCT sessions.game_id) AS games_count,
    COALESCE(SUM(sessions.hours), 0) AS hours
FROM users
LEFT JOIN sessions
    ON sessions.user_id = users.id
    AND sessions.is_cancelled = 0
GROUP BY users.id, users.name
ORDER BY hours DESC, users.name;

-- 18. Игры, в которые сыграно не меньше заданного числа часов.
-- [JOIN] [агрегат] [GROUP BY] [HAVING]
-- Страница «Статистика» (/statistics/?min_hours=10).
-- WHERE отбирает активные сессии до группировки,
-- HAVING - игры по сумме часов после группировки.
SELECT
    games.id,
    games.title,
    COUNT(sessions.id) AS sessions_count,
    SUM(sessions.hours) AS hours
FROM games
JOIN sessions
    ON sessions.game_id = games.id
WHERE sessions.is_cancelled = 0
GROUP BY games.id, games.title
HAVING SUM(sessions.hours) >= 10
ORDER BY hours DESC;
