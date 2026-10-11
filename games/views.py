"""View-функции приложения games.

Страницы строятся по объектам Game из JSON-хранилища ПР3: view-функции
загружают данные функциями storage, находят игру по идентификатору и
вызывают методы предметной модели, не дублируя её логику.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from homepage.views import (
    back_link,
    facts_list,
    not_found,
    page,
    table_section,
)
from models.games import find_game_by_id
from models.progress import COMPLETED, IN_PROGRESS, Progress
from models.sessions import (
    DATE_FORMAT,
    active_sessions,
    game_progress,
    hours_played,
)
from storage import load_library

# Приглушённые бейджи Bootstrap 5.3: светлый фон и тёмный текст цвета.
STATUS_BADGES: dict[str, str] = {
    COMPLETED: "bg-success-subtle text-success-emphasis",
    IN_PROGRESS: "bg-warning-subtle text-warning-emphasis",
}
DEFAULT_BADGE = "bg-secondary-subtle text-secondary-emphasis"


def progress_html(progress: Progress) -> str:
    """Вернуть шкалу прогресса Bootstrap со статусом прохождения.

    Процент, статус и оставшиеся часы - вычисляемые свойства объекта
    Progress из ПР3. Функцию использует и приложение gamesessions.
    """
    badge = STATUS_BADGES.get(progress.status, DEFAULT_BADGE)
    return f"""
    <div class="d-flex justify-content-between align-items-center mb-2">
        <span class="badge rounded-pill {badge}">{progress.status}</span>
        <span class="fw-semibold">{progress.percent:.0f}%</span>
    </div>
    <div class="progress mb-2" role="progressbar"
         aria-valuenow="{progress.percent:.0f}"
         aria-valuemin="0" aria-valuemax="100">
        <div class="progress-bar" style="width: {progress.percent:.0f}%">
        </div>
    </div>
    <div class="small text-muted">
        {progress.hours:.1f} из {progress.game.hours_total:.0f} ч,
        осталось {progress.hours_left:.1f} ч
    </div>
    """


def games(request: HttpRequest) -> HttpResponse:
    """Страница /games/: список игр библиотеки из data/games.json."""
    games_list, _, sessions_list = load_library(settings.DATA_DIR)
    rows = ""
    for game in games_list:
        url = reverse("game_detail", args=[game.id])
        played = hours_played(sessions_list, game=game)
        rows += f"""
        <tr>
            <td class="text-muted">{game.id}</td>
            <td><a href="{url}" class="fw-medium">{escape(game.title)}</a></td>
            <td>{escape(game.genre)}</td>
            <td>{escape(game.platform)}</td>
            <td>{game.release_year}</td>
            <td>{game.rating_label()}</td>
            <td class="text-end">{played:.1f} ч</td>
        </tr>
        """
    header = (
        "<th>ID</th><th>Название</th><th>Жанр</th><th>Платформа</th>"
        '<th>Год</th><th>Оценка</th><th class="text-end">Сыграно всеми</th>'
    )
    content = table_section("Игры", header, rows)
    return HttpResponse(
        page("Игровая библиотека - игры", content, active="games")
    )


def game_detail(request: HttpRequest, game_id: int) -> HttpResponse:
    """Страница /games/<id>/: карточка игры и прогресс игроков.

    Если игры с таким идентификатором нет, возвращается код 404.
    """
    games_list, users_list, sessions_list = load_library(settings.DATA_DIR)
    game = find_game_by_id(games_list, game_id)
    if game is None:
        return not_found(
            "Игра не найдена", reverse("games"), "← к списку игр"
        )

    facts = facts_list([
        ("Жанр", escape(game.genre)),
        ("Платформа", escape(game.platform)),
        ("Год выпуска", f"{game.release_year}, {game.era()}"),
        ("Время прохождения", f"{game.hours_total:.0f} ч"),
        ("Оценка", game.rating_label()),
        ("ID", str(game.id)),
    ])
    players = "".join(
        f"""
        <div class="panel p-3 mb-3">
            <div class="fw-semibold mb-2">{escape(progress.user.name)}</div>
            {progress_html(progress)}
        </div>
        """
        for progress in game_progress(sessions_list, users_list, game)
    )
    history = "".join(
        f"""
        <li>
            <a href="{reverse('session_detail', args=[session.id])}">
                {session.date.strftime(DATE_FORMAT)}
            </a>
            <span class="text-muted">
                {escape(session.user.name)}, {session.hours:.1f} ч
            </span>
        </li>
        """
        for session in active_sessions(sessions_list, game=game)
    ) or '<li class="text-muted">Сессий пока нет</li>'

    content = f"""
    {back_link(reverse('games'), 'Игры')}
    <h1 class="mb-4">{escape(game.title)}</h1>
    <div class="row g-4">
        <div class="col-lg-5">
            <div class="panel p-4">{facts}</div>
        </div>
        <div class="col-lg-7">
            <h2 class="h5 mb-3">Прогресс игроков</h2>
            {players}
            <h2 class="h5 mt-4 mb-3">Активные сессии</h2>
            <ul class="panel plain-list list-unstyled">{history}</ul>
        </div>
    </div>
    """
    return HttpResponse(page(game.title, content, active="games"))
