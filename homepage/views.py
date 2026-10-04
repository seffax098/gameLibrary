"""View-функции приложения homepage.

Здесь же находится общий каркас страниц проекта - функция page().
Главная страница - точка входа в проект и задаёт вид остальных
страниц, поэтому приложения games и gamesessions импортируют page()
и not_found() отсюда.
"""

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import escape

from stats import library_stats
from storage import load_library

BOOTSTRAP_CSS = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
    "/dist/css/bootstrap.min.css"
)

NAV_LINKS: tuple[tuple[str, str], ...] = (
    ("index", "Главная"),
    ("games", "Игры"),
    ("sessions", "Игровые сессии"),
)


def page(title, content):
    """Собрать HTML-документ страницы.

    Каркас общий для всех страниц: кодировка, заголовок вкладки,
    подключение Bootstrap 5.3 через CDN, навигация и контейнер с
    содержимым. Заголовок экранируется здесь, содержимое передаётся
    уже готовой HTML-разметкой.
    """
    links = "".join(
        f'<li class="nav-item">'
        f'<a class="nav-link" href="{reverse(name)}">{text}</a></li>'
        for name, text in NAV_LINKS
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="{BOOTSTRAP_CSS}">
    <style>
        body {{ background-color: #f4f5f9; }}
        main h1 {{ margin-bottom: 1.25rem; }}
        .stat-value {{ font-size: 1.75rem; font-weight: 600; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand bg-dark mb-4" data-bs-theme="dark">
        <div class="container flex-wrap">
            <a class="navbar-brand" href="{reverse('index')}">
                Игровая библиотека
            </a>
            <ul class="navbar-nav">{links}</ul>
        </div>
    </nav>
    <main class="container pb-5">{content}</main>
</body>
</html>"""


def not_found(message, back_url, back_text):
    """Вернуть страницу с сообщением об ошибке и кодом статуса 404."""
    content = f"""
    <h1 class="text-danger">{escape(message)}</h1>
    <a href="{back_url}" class="btn btn-outline-secondary">{back_text}</a>
    """
    return HttpResponse(page(message, content), status=404)


def stat_card(label, value):
    """Вернуть карточку с одним показателем сводки."""
    return f"""
    <div class="col-6 col-lg">
        <div class="card h-100 shadow-sm">
            <div class="card-body">
                <div class="text-muted small">{label}</div>
                <div class="stat-value">{value}</div>
            </div>
        </div>
    </div>
    """


def ranking_item(name, hours):
    """Вернуть строку рейтинга: название и сыгранные часы."""
    return (
        '<li class="list-group-item d-flex justify-content-between">'
        f'{name}<span class="badge bg-primary">{hours:.1f} ч</span></li>'
    )


def index(request):
    """Главная страница: описание библиотеки, сводка и навигация."""
    games, users, sessions = load_library(settings.DATA_DIR)
    stats = library_stats(games, users, sessions)

    cards = "".join((
        stat_card("Игр в библиотеке", stats["games"]),
        stat_card("Игроков", stats["users"]),
        stat_card("Активных сессий", stats["sessions"]),
        stat_card("Сыграно часов", f"{stats['hours']:.1f}"),
        stat_card("Средняя оценка", f"{stats['average_rating']:.1f}"),
    ))
    top_games = "".join(
        ranking_item(
            f'<a href="{reverse("game_detail", args=[game.id])}">'
            f"{escape(game.title)}</a>",
            hours,
        )
        for game, hours in stats["top"]
    )
    top_players = "".join(
        ranking_item(escape(user.name), hours)
        for user, hours in stats["players"]
    )

    content = f"""
    <div class="p-4 mb-4 bg-white rounded-3 shadow-sm">
        <h1 class="display-5">Игровая библиотека</h1>
        <p class="lead">
            Учёт общей коллекции видеоигр: игры, игровые сессии и личный
            прогресс прохождения каждого игрока.
        </p>
        <p>Основные разделы:</p>
        <a href="{reverse('games')}" class="btn btn-primary me-2">Игры</a>
        <a href="{reverse('sessions')}" class="btn btn-secondary">
            Игровые сессии
        </a>
    </div>
    <div class="row g-3 mb-4">{cards}</div>
    <div class="row g-3">
        <div class="col-md-6">
            <h2 class="h4">Популярные игры</h2>
            <ul class="list-group shadow-sm">{top_games}</ul>
        </div>
        <div class="col-md-6">
            <h2 class="h4">Самые активные игроки</h2>
            <ul class="list-group shadow-sm">{top_players}</ul>
        </div>
    </div>
    """
    return HttpResponse(page("Игровая библиотека", content))
