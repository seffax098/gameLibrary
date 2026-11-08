# Система управления игровой библиотекой

Github - https://github.com/seffax098/gameLibrary

Приложение для учёта общей коллекции видеоигр: игры, пользователи,
игровые сессии, личный прогресс прохождения каждого игрока, поиск,
сортировка и статистика библиотеки. Консольная версия (ПР3) дополнена
веб-интерфейсом на Django (ПР5), который в ПР6 переведён на шаблоны
Django и собственные статические файлы, а в ПР7 получает данные из
базы SQLite SQL-запросами. В ПР9 веб-интерфейс переведён на Django ORM.

## Используемые технологии

- Python 3.10+, Django 5.2;
- SQLite, Django ORM и миграции. SQL и `sqlite3` используются для данных ПР7;
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
- поиск игр — по названию, платформе, году выпуска и минимальной оценке;
- история сессий — поиск по игре или игроку, фильтры по игре, игроку и
  дате, сортировка и страницы по пять записей;
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

Представления получают данные через Django ORM и передают их шаблонам
через контекст `render()`.

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

В модели сессии дата задана полем `DateField`. Шаблоны отображают её
в формате `d.m.Y` фильтром `date`.

### Статические файлы

```text
homepage/static/homepage/
├── css/style.css    — собственное оформление (цвета, панели, статусы)
├── js/main.js       — год в подвале и поиск по таблице игр
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

## Модели Django и перенос данных (ПР9)

Веб-интерфейс читает `db.sqlite3`. Миграции `games` и `gamesessions`
создают три таблицы с первичными ключами `id`.

| Модель | Поля |
|---|---|
| `games.Game` | `title`, `genre`, `platform`, `release_year`, `hours_total`, `rating` (1–10 или `NULL`) |
| `gamesessions.Player` | `name`, уникальный `email` |
| `gamesessions.GameSession` | `game`, `player`, `session_date`, `hours`, `is_cancelled` (по умолчанию `False`) |

Сессия связана с игрой и игроком через два `ForeignKey`. Через обратную
связь `sessions` доступны сессии игры и игрока. `CASCADE` удаляет
зависимые сессии при удалении игры или игрока. Ограничение уникальности
допускает только одну активную сессию игрока по игре за день. Прогресс
вычисляется по активным сессиям и отображается отдельно для каждого игрока.

После миграций команда `python manage.py import_library` переносит данные
из `data/gamelibrary.sqlite` в `db.sqlite3`. Исходная база открывается
для чтения. Игры и игроки переносятся перед сессиями, их идентификаторы
и связи сохраняются. Команда работает в одной транзакции. Повторный
запуск обновляет строки с теми же ID и не создаёт дубликатов. Для другой
исходной базы укажите `--source ПУТЬ`. В исходном наборе 4 игры,
2 игрока и 6 сессий, одна из которых отменена.

### Запросы ORM

| Страница | Запросы и операции |
|---|---|
| `/games/` | Список с `Sum` активных часов и сортировкой по ID |
| `/games/<id>/` | Игра через `get()`, часы по каждому игроку через `annotate()`, активные сессии с `select_related("player")` |
| `/games/search/` | Уникальные платформы через `values_list().distinct()`, выборка игр по платформе, году и оценке, поиск по названию, сортировка по оценке и названию |
| `/games/unplayed/` | Список игроков, выборка ID игр с активными сессиями игрока, `exclude()` игр из этого подзапроса |
| `/sessions/` | Связи через `select_related("player", "game")`, фильтры по игре, игроку и дате, поиск по `game__title` или `player__name`, сортировка и `Paginator` |
| `/sessions/<id>/` | Одна сессия со связанными объектами, сумма часов по игроку и игре |
| `/` | Сводные показатели игр, игроков и сессий, две тройки лидеров по активным часам |
| `/statistics/` | Группировка по жанрам и платформам, аннотации по игрокам, игры с суммой часов выше заданного порога |

CRUD можно проверить на тестовой записи в `python manage.py shell`.

```python
from games.models import Game

game = Game.objects.create(
    title="Проверка CRUD", platform="PC", release_year=2020, hours_total=2
)
game = Game.objects.get(pk=game.pk)
game.rating = 8
game.save(update_fields=["rating"])
game.delete()
```

## База данных SQLite (ПР7)

Схема и запросы ПР7 сохранены как исходная реализация. Консольная
версия работает с JSON через `storage.py`. Команда
`python -m db.import_json` обновляет исходную базу ПР7 из JSON.

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

`db/database.py` не зависит от Django. Настройка `LIBRARY_DB` в
`settings.py` задаёт источник данных для команды переноса ПР9.

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
├── games/            — модель игры, миграция и страницы игр
├── gamesessions/     — игроки, сессии, миграция, страницы и команда импорта
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
python manage.py import_library
python manage.py runserver
```

Веб-интерфейс: http://127.0.0.1:8000/. Консольная версия:
`python main.py`. Для добавления и обновления записей из JSON сначала
выполните `python -m db.import_json`, затем `python manage.py import_library`.
Удалённые из JSON записи команда переноса оставляет в базе Django.

## Тесты и проверка кода

```text
python manage.py check
python manage.py showmigrations
python manage.py test     — тесты веб-страниц
pytest -v                 — тесты предметной области и базы данных
flake8 . --extend-exclude=venv
mypy .
pylint --recursive=y .
python manage.py findstatic homepage/img/logo.png
```

Тесты страниц создают ORM-объекты в тестовой базе Django и проверяют
маршруты, шаблоны, ответы 404, статистику, поиск, фильтрацию, сортировку,
пагинацию и ограничение на активные сессии.

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
  базы; добавлены поиск игр, «Что поиграть» и статистика;
- **ПР9** — модели Django, миграции, перенос данных, ORM-запросы
  во всех представлениях, серверный поиск и пагинация.

Коммиты практических работ начинаются с метки номера работы, например
`PR7:`.
