# Система управления игровой библиотекой

Github - https://github.com/seffax098/gameLibrary

Приложение для учёта общей коллекции видеоигр: игры, пользователи,
игровые сессии, личный прогресс прохождения каждого игрока, поиск,
сортировка и статистика библиотеки. Консольная версия (ПР3) дополнена
веб-интерфейсом на Django (ПР5), который в ПР6 переведён на шаблоны
Django и собственные статические файлы.

## Используемые технологии

- Python 3.10+, Django 5.2;
- Django Template Language (DTL), HTML5, CSS3, JavaScript;
- Bootstrap 5.3 (CDN);
- JSON для хранения данных;
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
| `/games/` | `games:list` | `games.views.games()` | `games/game_list.html` |
| `/games/<int:game_id>/` | `games:detail` | `games.views.game_detail()` | `games/game_detail.html` |
| `/sessions/` | `gamesessions:list` | `gamesessions.views.sessions()` | `gamesessions/session_list.html` |
| `/sessions/<int:session_id>/` | `gamesessions:detail` | `gamesessions.views.session_detail()` | `gamesessions/session_detail.html` |

- главная — сводка библиотеки, популярные игры и самые активные игроки;
- карточка игры — характеристики, прогресс каждого игрока, активные сессии;
- карточка сессии — связанные игра и игрок, прогресс игрока в игре.

Приложения: `homepage` (главная, страница 404, статические файлы),
`games`, `gamesessions` (название `sessions` занято встроенным
`django.contrib.sessions`). Изменение данных (добавление игр, запись и
отмена сессий) пока доступно только в консольной версии — для веба
нужны формы.

View-функции не формируют HTML: они загружают данные функциями ПР3,
собирают словарь контекста и вызывают `render()`. Функция `page()` из
ПР5, собиравшая HTML в Python-строке, удалена.

```python
def sessions(request):
    _, _, sessions_list = load_library(settings.DATA_DIR)
    context = {"sessions": sorted(sessions_list, key=lambda item: item.date)}
    return render(request, "gamesessions/session_list.html", context)
```

### Шаблоны Django

```text
templates/                      — шаблоны уровня проекта (DIRS в settings.py)
├── base.html                   — базовый шаблон всех страниц
├── 404.html                    — страница «Страница не найдена»
└── includes/                   — navigation.html, back_link.html, not_found.html
homepage/templates/homepage/    — index.html, includes/stat_card.html, ranking_item.html
games/templates/games/          — game_list.html, game_detail.html,
                                  includes/game_row.html, progress.html
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
| `date` | `{{ session.date\|date:"d.m.Y" }}` |
| `floatformat` | `{{ session.hours\|floatformat:1 }} ч` |

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

Данные хранятся в JSON-файлах `data/games.json`, `data/users.json`,
`data/sessions.json` и загружаются модулем `storage.py`
(`load_library()`) в объекты классов из пакета `models/`. Сессии
хранят ссылки идентификаторами `user_id` и `game_id`. Django ORM и база
данных пока не используются.

## Структура проекта

```text
gameLibrary/
├── manage.py
├── main.py           — консольная версия
├── storage.py        — загрузка и сохранение JSON
├── stats.py          — статистика библиотеки
├── utils.py          — безопасный ввод для консоли
├── gamelibrary/      — настройки Django-проекта и корневой urls.py
├── templates/        — base.html, 404.html, includes/
├── homepage/         — главная страница, static/, templates/
├── games/            — страницы игр
├── gamesessions/     — страницы игровых сессий
├── models/           — классы Game, User, GameSession, Progress
├── data/             — JSON-файлы с данными
└── tests/            — тесты предметной области (pytest)
```

## Запуск

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Веб-интерфейс: http://127.0.0.1:8000/. Консольная версия:
`python main.py`. Обе версии работают с одними файлами `data/*.json`.

## Тесты и проверка кода

```text
python manage.py check
python manage.py test     — тесты веб-страниц
pytest -v                 — тесты предметной области
flake8 .
mypy .
python manage.py findstatic homepage/img/logo.png
```

Тесты страниц используют временный каталог с тестовыми данными и
проверяют маршруты и пространства имён, используемые шаблоны и контекст,
коды 200 и 404, пустые коллекции, экранирование и подключение
статических файлов.

## Развитие проекта

- **ПР1–ПР3** — от сценария на переменных к функциям, JSON-хранению и
  объектной модели;
- **ПР5** — веб-интерфейс на Django: проект, приложения, маршруты, views;
- **ПР6** — шаблоны Django, контекст, фильтры, пространства имён URL,
  собственные CSS, JavaScript и изображение.

Коммиты практических работ начинаются с метки номера работы, например
`PR6:`.

Не реализовано: Django ORM и база данных, формы Django, вход
пользователей. Следующие этапы — перенос данных из JSON в базу данных и
Django ORM, формы для добавления игр и записи сессий, аутентификация,
API.
