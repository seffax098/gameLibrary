# Система управления игровой библиотекой

Github - https://github.com/seffax098/gameLibrary

Приложение для учёта общей коллекции видеоигр: игры, пользователи,
игровые сессии, личный прогресс прохождения каждого игрока, поиск,
сортировка и статистика библиотеки. Консольная версия (ПР3) дополнена
веб-интерфейсом на Django (ПР5), который в ПР6 переведён на шаблоны
Django и собственные статические файлы, а в ПР7 получает данные из
базы SQLite SQL-запросами.

## Используемые технологии

- Python 3.10+, Django 5.2;
- SQLite, SQL, модуль `sqlite3` стандартной библиотеки Python;
- Django Template Language (DTL), HTML5, CSS3, JavaScript;
- Bootstrap 5.3 (CDN);
- JSON — исходные данные и хранилище консольной версии;
- pytest и `django.test`, flake8, mypy (`django-stubs`), pylint.

## Предметная область

Библиотека содержит игры (жанр, платформа, год выпуска, время
прохождения, оценка). Пользователи записывают игровые сессии: кто, во
что, в какой день и сколько часов играл. По сессиям вычисляется личный
прогресс каждого игрока в каждой игре.

| Класс | Атрибуты | Назначение |
|---|---|---|
| `Game` | `id`, `title`, `genre`, `platform`, `release_year`, `hours_total`, `rating` | игра; проверка данных, эпоха, описание оценки |
| `User` | `id`, `name`, `email` | игрок; проверка имени и почты |
| `GameSession` | `id`, `user`, `game`, `date`, `hours`, `is_cancelled` | сессия; ссылается на объекты `User` и `Game`, может быть отменена |
| `Progress` | `user`, `game`, `hours` | прогресс игрока: процент, статус, оставшееся время |

Правила: у пользователя одна активная сессия по игре за день; отменённая
сессия остаётся в истории, но не учитывается в прогрессе; прогресс
личный для каждого игрока; почта пользователя уникальна.

## Веб-интерфейс

| URL | Имя маршрута | View-функция | Шаблон |
|---|---|---|---|
| `/` | `homepage:index` | `homepage.views.index()` | `homepage/index.html` |
| `/statistics/` | `homepage:statistics` | `homepage.views.statistics()` | `homepage/statistics.html` |
| `/games/` | `games:list` | `games.views.games()` | `games/game_list.html` |
| `/games/search/` | `games:search` | `games.views.game_search()` | `games/game_search.html` |
| `/games/unplayed/` | `games:unplayed` | `games.views.unplayed_games()` | `games/game_unplayed.html` |
| `/games/<int:game_id>/` | `games:detail` | `games.views.game_detail()` | `games/game_detail.html` |
| `/sessions/` | `gamesessions:list` | `gamesessions.views.sessions()` | `gamesessions/session_list.html` |
| `/sessions/<int:session_id>/` | `gamesessions:detail` | `gamesessions.views.session_detail()` | `gamesessions/session_detail.html` |

- главная — сводка библиотеки, популярные игры и самые активные игроки;
- статистика — жанры, платформы, активность игроков, игры с заданным
  числом сыгранных часов;
- поиск игр — по платформе, году выпуска и минимальной оценке;
- «Что поиграть» — игры, в которые выбранный игрок ещё не играл;
- карточка игры — характеристики, прогресс каждого игрока, активные сессии;
- карточка сессии — связанные игра и игрок, прогресс игрока в игре.

Навигация: Главная | Игры | Игровые сессии | Статистика. Поиск игр и
«Что поиграть» — функции раздела «Игры», ссылки на них стоят на
странице списка игр. Все ссылки строятся по именам маршрутов.

Приложения: `homepage` (главная, статистика, страница 404, статические
файлы), `games`, `gamesessions` (название `sessions` занято встроенным
`django.contrib.sessions`). Изменение данных (добавление игр, запись и
отмена сессий) пока доступно только в консольной версии — для веба
нужны формы.

View-функции не формируют HTML: они выполняют SQL-запрос к базе SQLite,
передают результат в контекст и вызывают `render()` (подробнее — в
разделе «База данных SQLite»).

### Шаблоны Django

```text
templates/                      — шаблоны уровня проекта (DIRS в settings.py)
├── base.html                   — базовый шаблон всех страниц
├── 404.html                    — страница «Страница не найдена»
└── includes/                   — navigation.html, back_link.html, not_found.html
homepage/templates/homepage/    — index.html, statistics.html,
                                  includes/stat_card.html, ranking_item.html
games/templates/games/          — game_list.html, game_detail.html,
                                  game_search.html, game_unplayed.html,
                                  includes/game_row.html, progress.html
games/templatetags/             — game_filters.py: фильтр rating_label
gamesessions/templates/gamesessions/
                                — session_list.html, session_detail.html,
                                  includes/session_status.html
```

- **Наследование.** `base.html` содержит общую структуру: `head`,
  Bootstrap, собственный CSS, навигацию, подвал, JavaScript. Дочерние
  шаблоны начинаются с `{% extends "base.html" %}` и переопределяют
  блоки `{% block title %}` и `{% block content %}`; заголовок вкладки
  дополняется через `{{ block.super }}`.
- **Включаемые шаблоны.** Повторяющиеся фрагменты подключаются через
  `{% include %}`: навигация, строка таблицы игр, шкала прогресса (на
  страницах игры и сессии), статус сессии (в списке и карточке).
- **Циклы и условия.** `{% for %}` выводит игры, сессии и прогресс,
  `{% empty %}` — сообщение для пустой коллекции, `{% if %}` — статус
  сессии (`session.is_cancelled`), статус прохождения и случай, когда
  объект не найден.
- **Ссылки** строятся по именам маршрутов с пространствами имён
  (`app_name` в `urls.py` приложений): `{% url 'games:detail' game.id %}`.
- **Экранирование.** Значения `{{ ... }}` экранируются автоматически.

### Фильтры шаблонов

| Фильтр | Пример |
|---|---|
| `length` | `Всего игр: {{ games\|length }}` |
| `default` | `{{ game.title\|default:"Без названия" }}` |
| `floatformat` | `{{ session.hours\|floatformat:1 }} ч` |
| `rating_label` (свой) | `{{ game.rating\|rating_label }}` → «10/10 - шедевр», для `NULL` — «не выставлена» |

Даты сессий хранятся в базе строкой `YYYY-MM-DD` и форматируются в
запросе: `strftime('%d.%m.%Y', session_date) AS played_on`.

### Статические файлы

```text
homepage/static/homepage/
├── css/style.css    — собственное оформление (цвета, панели, статусы)
├── js/main.js       — год в подвале и поиск по таблицам игр и сессий
└── img/logo.png     — логотип в шапке и значок вкладки
```

Файлы подключаются в `base.html` через `{% load static %}` и
`{% static 'homepage/css/style.css' %}`. Bootstrap используется для
базовой вёрстки, собственный CSS — для оформления проекта.

### Ошибка 404

- `/games/999/` — маршрут есть, объекта нет: в шаблон передаётся
  `{"game": None}`, срабатывает ветка `{% else %}`, `render()` получает
  `status=404`;
- `/nonexistent/`, `/games/abc/` — маршрута нет: вызывается
  `handler404` (`homepage.views.page_not_found`), шаблон `404.html`.
  Собственная страница видна только при `DEBUG = False`.

## Хранение данных

Исходные данные лежат в JSON-файлах `data/games.json`, `data/users.json`,
`data/sessions.json`. Консольная версия по-прежнему работает с ними
через модуль `storage.py` (`load_library()`, объекты из пакета
`models/`). Веб-интерфейс с ПР7 читает данные из базы SQLite
`data/gamelibrary.sqlite`, куда они переносятся из JSON скриптом
`db/import_json.py`.

```text
до ПР7:    JSON → storage.py → объекты Python → view → шаблон
после ПР7: JSON ──(db/import_json.py)──→ SQLite
           SQLite → SQL → sqlite3 (sqlite3.Row) → view → context → шаблон
```

## База данных SQLite (ПР7)

### Структура

Сущности предметной области — игра, пользователь, игровая сессия —
представлены тремя таблицами. Связи: у игры и у пользователя может
быть много сессий, каждая сессия относится к одному пользователю и
одной игре.

Таблица `games` — игры библиотеки:

| Поле | Тип | Назначение |
|---|---|---|
| `id` | `INTEGER` | первичный ключ |
| `title` | `TEXT NOT NULL` | название |
| `genre` | `TEXT NOT NULL` | жанр |
| `platform` | `TEXT NOT NULL` | платформа |
| `release_year` | `INTEGER NOT NULL` | год выпуска |
| `hours_total` | `REAL NOT NULL` | примерное время прохождения, ч |
| `rating` | `INTEGER` | оценка 1–10; `NULL` — не выставлена |

Таблица `users` — игроки:

| Поле | Тип | Назначение |
|---|---|---|
| `id` | `INTEGER` | первичный ключ |
| `name` | `TEXT NOT NULL` | имя |
| `email` | `TEXT NOT NULL UNIQUE` | почта, уникальна |

Таблица `sessions` — игровые сессии:

| Поле | Тип | Назначение |
|---|---|---|
| `id` | `INTEGER` | первичный ключ |
| `user_id` | `INTEGER NOT NULL` | внешний ключ → `users.id` |
| `game_id` | `INTEGER NOT NULL` | внешний ключ → `games.id` |
| `session_date` | `TEXT NOT NULL` | дата `YYYY-MM-DD` (сортируется как строка) |
| `hours` | `REAL NOT NULL` | сыграно часов |
| `is_cancelled` | `INTEGER NOT NULL DEFAULT 0` | 0 — активна, 1 — отменена |

```text
users                 sessions                  games
id PK  ◄────────────  user_id FK
                      game_id FK  ────────────► id PK
```

- **Первичные ключи** `id` однозначно определяют запись и позволяют
  ссылаться на неё из других таблиц.
- **Внешние ключи** `sessions.user_id` и `sessions.game_id` не дают
  записать сессию несуществующего игрока или игры. SQLite проверяет их
  только после `PRAGMA foreign_keys = ON` — она выполняется при каждом
  подключении в `db/database.py`.
- **Отсутствие значения** допустимо только для оценки игры: в JSON
  «не выставлена» записывалось как 0, в базе это `NULL`. Поэтому
  `AVG(rating)` сам пропускает игры без оценки.

### Файлы

```text
sql/schema.sql        — CREATE TABLE IF NOT EXISTS для трёх таблиц
sql/queries.sql       — 18 проверенных запросов проекта с комментариями
db/database.py        — get_connection(), create_schema(), fetch_all(), fetch_one()
db/import_json.py     — перенос JSON → SQLite
data/gamelibrary.sqlite — файл базы данных
```

`db/database.py` не зависит от Django. Путь к базе для веб-интерфейса
задаёт настройка `LIBRARY_DB` в `settings.py` (тесты подменяют её
временной базой). Служебная база Django `db.sqlite3` — отдельный файл.

### Создание базы и перенос данных

```text
python -m db.import_json
```

Скрипт создаёт таблицы по `sql/schema.sql`, очищает их и переносит
данные из JSON (`executemany()` с параметрами `?`), затем сравнивает
число записей:

```text
games: JSON 4 -> SQLite 4
users: JSON 2 -> SQLite 2
sessions: JSON 6 -> SQLite 6
```

- порядок импорта: `games` и `users`, затем `sessions` — сессии
  ссылаются на них внешними ключами; очистка идёт в обратном порядке;
- преобразования: оценка `0` → `NULL`, `is_cancelled` `true/false` →
  `1/0`, поле `date` → `session_date`;
- весь перенос — одна транзакция: `commit()` при успехе, `rollback()`
  при ошибке, база остаётся прежней;
- скрипт можно запускать повторно — база заново совпадёт с JSON.


### SQL-запросы

Все запросы сохранены в `sql/queries.sql` с комментарием о назначении и
странице, где используются. Проверка в SQLite CLI:

```text
sqlite3 -header -column data/gamelibrary.sqlite < sql/queries.sql
```

| № | Запрос | Вид | Страница |
|---|---|---|---|
| 1 | игры с часами всех игроков (`LEFT JOIN`, `SUM`, `COALESCE`) | список, JOIN, агрегат, GROUP BY | `/games/` |
| 2 | карточка игры по `id` | WHERE | `/games/<id>/` |
| 3 | часы каждого игрока в игре | JOIN, агрегат, GROUP BY | `/games/<id>/` |
| 4 | активные сессии игры с именами игроков | JOIN, WHERE | `/games/<id>/` |
| 5 | платформы без повторов (`DISTINCT`) | список | `/games/search/` |
| 6 | поиск по платформе, году и оценке | WHERE (несколько условий) | `/games/search/` |
| 7 | список игроков | список | `/games/unplayed/` |
| 8 | игры, в которые игрок не играл (`NOT IN`) | WHERE, подзапрос | `/games/unplayed/` |
| 9 | все сессии с игроком и игрой | список, JOIN | `/sessions/` |
| 10 | карточка сессии с игроком и игрой | JOIN, WHERE | `/sessions/<id>/` |
| 11 | часы игрока в игре | агрегат, WHERE | `/sessions/<id>/` |
| 12 | сводка: `COUNT`, `SUM`, `AVG` | агрегат | `/` |
| 13 | три популярные игры (`LIMIT 3`) | JOIN, агрегат, GROUP BY | `/` |
| 14 | три самых активных игрока | JOIN, агрегат, GROUP BY | `/` |
| 15 | игры и средняя оценка по жанрам | агрегат, GROUP BY | `/statistics/` |
| 16 | игры и годы выпуска по платформам (`MIN`, `MAX`) | агрегат, GROUP BY | `/statistics/` |
| 17 | активность игроков (`COUNT(DISTINCT)`) | JOIN, агрегат, GROUP BY | `/statistics/` |
| 18 | игры, в которые сыграно ≥ N часов | JOIN, GROUP BY, HAVING | `/statistics/` |

Соответствие операциям прежней реализации: поиск в Python → `WHERE`,
`sorted()` → `ORDER BY`, срез списка → `LIMIT`, `sum()`/`len()` →
`SUM()`/`COUNT()`, подсчёт по словарю в `stats.py` → `GROUP BY`.

### Получение данных в Django

View-функции передают SQL-запрос и параметры в `fetch_all()` или
`fetch_one()` из `db/database.py`. Там соединение настраивается
`conn.row_factory = sqlite3.Row`, поэтому к полям результата можно
обращаться по имени: `row["title"]` в Python, `{{ game.title }}` в
шаблоне. Строки передаются в шаблон через контекст:

```python
def unplayed_games(request):
    ...
    games_list = fetch_all(
        settings.LIBRARY_DB,
        """
        SELECT games.id, games.title, ...
        FROM games
        WHERE games.id NOT IN (
            SELECT sessions.game_id
            FROM sessions
            WHERE sessions.user_id = ?
                AND sessions.is_cancelled = 0
        )
        ORDER BY games.title
        """,
        [user_id],
    )
    return render(request, "games/game_unplayed.html", {"games": games_list, ...})
```

- Значения от пользователя (платформа, год, оценка, игрок, порог
  часов) передаются **параметрами `?`**, а не f-строками или
  конкатенацией: значение не становится частью текста SQL и не может
  его изменить. Например, `?platform=' OR 1=1 --` просто ничего не
  находит.
- Нечисловые значения параметров (`?year_from=abc`) не вызывают ошибку:
  применяется значение по умолчанию.
- В карточках игры и сессии строки превращаются в объекты `Game`,
  `User`, `Progress`: эпоху игры, описание оценки, процент и статус
  прохождения по-прежнему вычисляет объектная модель.
- Пустой результат запроса — не ошибка: шаблоны выводят сообщение через
  `{% empty %}`. Если файла базы нет, страница сообщает, что нужно
  выполнить `python -m db.import_json`, а не создаёт пустую базу.
- Изменения в базе сразу видны на сайте: после
  `UPDATE games SET title = 'Hades II' WHERE id = 2;` в `sqlite3`
  новое название появится на всех страницах после обновления.

## Структура проекта

```text
gameLibrary/
├── manage.py
├── main.py           — консольная версия
├── storage.py        — загрузка и сохранение JSON (консольная версия)
├── stats.py          — статистика библиотеки (консольная версия)
├── utils.py          — безопасный ввод для консоли
├── gamelibrary/      — настройки Django-проекта и корневой urls.py
├── templates/        — base.html, 404.html, includes/
├── homepage/         — главная, статистика, static/, templates/
├── games/            — страницы игр, поиск, «Что поиграть», templatetags/
├── gamesessions/     — страницы игровых сессий
├── models/           — классы Game, User, GameSession, Progress
├── db/               — подключение к SQLite и импорт из JSON
├── sql/              — schema.sql и queries.sql
├── data/             — JSON-файлы и база gamelibrary.sqlite
└── tests/            — тесты предметной области и базы данных (pytest)
```

## Запуск

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python -m db.import_json
python manage.py runserver
```

Веб-интерфейс: http://127.0.0.1:8000/. Консольная версия:
`python main.py` — она изменяет JSON-файлы; чтобы перенести изменения
на сайт, повторите `python -m db.import_json`.

## Тесты и проверка кода

```text
python manage.py check
python manage.py test     — тесты веб-страниц
pytest -v                 — тесты предметной области и базы данных
flake8 . --extend-exclude=venv
mypy .
python manage.py findstatic homepage/img/logo.png
```

Тесты страниц создают временные JSON-файлы, переносят их во временную
базу SQLite тем же `import_library()` и проверяют маршруты и
пространства имён, используемые шаблоны и контекст, коды 200 и 404,
пустые результаты, фильтрацию `WHERE`/`HAVING`, передачу значений
параметрами, экранирование и подключение статических файлов.

Тесты `tests/test_database.py` проверяют схему и внешние ключи, импорт
(число записей, преобразование значений, повторный запуск, откат при
ошибке) и выполняют каждый запрос из `sql/queries.sql`.

## Развитие проекта

- **ПР1–ПР3** — от сценария на переменных к функциям, JSON-хранению и
  объектной модели;
- **ПР5** — веб-интерфейс на Django: проект, приложения, маршруты, views;
- **ПР6** — шаблоны Django, контекст, фильтры, пространства имён URL,
  собственные CSS, JavaScript и изображение;
- **ПР7** — база данных SQLite: схема с первичными и внешними ключами,
  перенос данных из JSON, 18 SQL-запросов (`WHERE`, `JOIN`, агрегатные
  функции, `GROUP BY`, `HAVING`), страницы сайта получают данные из
  базы; добавлены поиск игр, «Что поиграть» и статистика.

Коммиты практических работ начинаются с метки номера работы, например
`PR7:`.

Не реализовано: Django ORM, формы Django, вход пользователей; изменение
данных через сайт. Следующие этапы — переход от SQL-запросов к моделям
Django и ORM, формы для добавления игр и записи сессий, аутентификация,
API.
