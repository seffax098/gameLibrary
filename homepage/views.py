"""View-функции приложения homepage.

Здесь же находится общий каркас страниц проекта - функция page() - и
небольшие функции оформления, общие для всех приложений. Главная
страница - точка входа в проект и задаёт вид остальных страниц,
поэтому приложения games и gamesessions импортируют их отсюда.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from stats import library_stats
from storage import load_library

BOOTSTRAP_CSS = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
    "/dist/css/bootstrap.min.css"
)
FONT_CSS = (
    "https://fonts.googleapis.com/css2"
    "?family=Inter:wght@400;500;600;700&display=swap"
)

NAV_LINKS: tuple[tuple[str, str], ...] = (
    ("index", "Главная"),
    ("games", "Игры"),
    ("sessions", "Игровые сессии"),
)

STYLES = """
:root {
    --ink: #111827;
    --muted: #6b7280;
    --line: #e5e7eb;
    --surface: #f9fafb;
    --accent: #4f46e5;
    --bs-body-font-family: "Inter", system-ui, sans-serif;
    --bs-body-color: var(--ink);
    --bs-body-bg: #ffffff;
    --bs-border-color: var(--line);
    --bs-link-color-rgb: 79, 70, 229;
    --bs-link-hover-color-rgb: 67, 56, 202;
}
body { -webkit-font-smoothing: antialiased; }
h1, h2 { font-weight: 600; letter-spacing: -0.02em; }
.site-nav { border-bottom: 1px solid var(--line); }
.site-nav .navbar-brand { font-weight: 700; color: var(--ink); }
.site-nav .nav-link { color: var(--muted); }
.site-nav .nav-link:hover,
.site-nav .nav-link.active { color: var(--ink); }
.site-nav .nav-link.active { font-weight: 500; }
.panel {
    border: 1px solid var(--line);
    border-radius: 12px;
    background: #ffffff;
}
.section-label {
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.stat-value { font-size: 1.75rem; font-weight: 600; }
.back-link { color: var(--muted); text-decoration: none; }
.back-link:hover { color: var(--ink); }
.table { margin-bottom: 0; }
.table th {
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: var(--surface);
}
.table td, .table th { padding: 0.85rem 1rem; }
.table a, .plain-list a { color: var(--ink); text-decoration: none; }
.table a:hover, .plain-list a:hover { color: var(--accent); }
.plain-list > li {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.85rem 1.25rem;
    border-top: 1px solid var(--line);
}
.plain-list > li:first-child { border-top: none; }
.fact-label { color: var(--muted); font-size: 0.8125rem; }
.progress { height: 6px; background: var(--line); }
.progress-bar { background: var(--accent); }
.btn { border-radius: 8px; padding: 0.5rem 1rem; font-weight: 500; }
"""


def page(title: str, content: str, active: str | None = None) -> str:
    """Собрать HTML-документ страницы.

    Каркас общий для всех страниц: кодировка, заголовок вкладки,
    подключение Bootstrap 5.3 и шрифта через CDN, навигация и контейнер
    с содержимым. active - имя маршрута раздела, который выделяется в
    навигации. Заголовок экранируется здесь, содержимое передаётся уже
    готовой HTML-разметкой.
    """
    links = ""
    for name, text in NAV_LINKS:
        state = ' active" aria-current="page' if name == active else ""
        links += (
            f'<li class="nav-item"><a class="nav-link{state}" '
            f'href="{reverse(name)}">{text}</a></li>'
        )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="{BOOTSTRAP_CSS}">
    <link rel="stylesheet" href="{FONT_CSS}">
    <style>{STYLES}</style>
</head>
<body>
    <nav class="navbar navbar-expand site-nav">
        <div class="container flex-wrap">
            <a class="navbar-brand" href="{reverse('index')}">
                Игровая библиотека
            </a>
            <ul class="navbar-nav">{links}</ul>
        </div>
    </nav>
    <main class="container py-5">{content}</main>
</body>
</html>"""


def back_link(url: str, text: str) -> str:
    """Вернуть ссылку «назад» над заголовком страницы."""
    return (
        f'<a href="{url}" class="back-link small d-inline-block mb-3">'
        f"← {text}</a>"
    )


def not_found(message: str, back_url: str, back_text: str) -> HttpResponse:
    """Вернуть страницу с сообщением об ошибке и кодом статуса 404."""
    content = f"""
    <p class="section-label mb-2">Ошибка 404</p>
    <h1 class="mb-4">{escape(message)}</h1>
    <a href="{back_url}" class="btn btn-outline-secondary">{back_text}</a>
    """
    return HttpResponse(page(message, content), status=404)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Обработчик ошибки 404 для всего проекта (handler404)..
    """
    return not_found(
        "Страница не найдена", reverse("index"), "← на главную"
    )


def table_section(heading: str, header: str, rows: str) -> str:
    """Вернуть раздел страницы: заголовок и таблицу в рамке.

    header - ячейки <th> строки заголовка, rows - строки <tr> таблицы.
    Таблица прокручивается внутри блока table-responsive, поэтому не
    растягивает страницу на узком экране.
    """
    return f"""
    <h1 class="mb-4">{heading}</h1>
    <div class="panel overflow-hidden">
        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead><tr>{header}</tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """


def facts_list(facts: list[tuple[str, str]]) -> str:
    """Вернуть сетку фактов карточки объекта: подпись над значением."""
    items = "".join(
        f'<div class="col"><div class="fact-label">{label}</div>'
        f"<div>{value}</div></div>"
        for label, value in facts
    )
    return f'<div class="row row-cols-2 g-4">{items}</div>'


def stat_card(label: str, value: object) -> str:
    """Вернуть карточку с одним показателем сводки."""
    return f"""
    <div class="col-6 col-lg">
        <div class="panel h-100 p-3">
            <div class="section-label mb-1">{label}</div>
            <div class="stat-value">{value}</div>
        </div>
    </div>
    """


def ranking_item(name: str, hours: float) -> str:
    """Вернуть строку рейтинга: название и сыгранные часы."""
    return f'<li>{name}<span class="text-muted">{hours:.1f} ч</span></li>'


def index(request: HttpRequest) -> HttpResponse:
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
    <section class="mb-5">
        <h1 class="display-6 mb-3">Игровая библиотека</h1>
        <p class="lead text-muted mb-4">
            Учёт общей коллекции видеоигр: игры, игровые сессии и личный
            прогресс прохождения каждого игрока.
        </p>
        <a href="{reverse('games')}" class="btn btn-outline-secondary">
            Игры
        </a>
        <a href="{reverse('sessions')}" class="btn btn-outline-secondary">
            Игровые сессии
        </a>
    </section>
    <div class="row g-3 mb-5">{cards}</div>
    <div class="row g-4">
        <div class="col-md-6">
            <h2 class="h5 mb-3">Популярные игры</h2>
            <ul class="panel plain-list list-unstyled">{top_games}</ul>
        </div>
        <div class="col-md-6">
            <h2 class="h5 mb-3">Самые активные игроки</h2>
            <ul class="panel plain-list list-unstyled">{top_players}</ul>
        </div>
    </div>
    """
    return HttpResponse(page("Игровая библиотека", content, active="index"))
