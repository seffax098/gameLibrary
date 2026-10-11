"""View-функции приложения games.

Страницы строятся по объектам Game из JSON-хранилища ПР3: view-функции
загружают данные функциями storage, находят игру по идентификатору и
вызывают методы предметной модели, не дублируя её логику.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from homepage.views import not_found, page, table_section
from models.games import find_game_by_id
from models.progress import COMPLETED, IN_PROGRESS, Progress
from models.sessions import (
    DATE_FORMAT,
    active_sessions,
    game_progress,
    hours_played,
)
from storage import load_library

STATUS_BADGES: dict[str, str] = {
    COMPLETED: "bg-success",
    IN_PROGRESS: "bg-warning text-dark",
}


def progress_html(progress: Progress) -> str:
    """Вернуть шкалу прогресса Bootstrap со статусом прохождения.

    Процент, статус и оставшиеся часы - вычисляемые свойства объекта
    Progress из ПР3. Функцию использует и приложение gamesessions.
    """
    badge = STATUS_BADGES.get(progress.status, "bg-secondary")
    return f"""
    <div class="d-flex justify-content-between small mb-1">
        <span>
            <span class="badge {badge}">{progress.status}</span>
            {progress.percent:.0f}%
        </span>
        <span>{progress.hours:.1f} из {progress.game.hours_total:.0f} ч,
              осталось {progress.hours_left:.1f} ч</span>
    </div>
    <div class="progress" role="progressbar"
         aria-valuenow="{progress.percent:.0f}"
         aria-valuemin="0" aria-valuemax="100">
        <div class="progress-bar" style="width: {progress.percent:.0f}%">
        </div>
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
            <td>{game.id}</td>
            <td><a href="{url}">{escape(game.title)}</a></td>
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
    return HttpResponse(page("Игровая библиотека - игры", content))


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

    players = "".join(
        f"""
        <li class="list-group-item">
            <div class="fw-semibold mb-1">{escape(progress.user.name)}</div>
            {progress_html(progress)}
        </li>
        """
        for progress in game_progress(sessions_list, users_list, game)
    )
    history = "".join(
        f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="{reverse('session_detail', args=[session.id])}">
                {session.date.strftime(DATE_FORMAT)}
            </a>
            <span>{escape(session.user.name)}, {session.hours:.1f} ч</span>
        </li>
        """
        for session in active_sessions(sessions_list, game=game)
    ) or '<li class="list-group-item text-muted">Сессий пока нет</li>'

    content = f"""
    <div class="row g-4">
        <div class="col-lg-5">
            <div class="card shadow-sm">
                <div class="card-body">
                    <h1 class="h3 card-title">{escape(game.title)}</h1>
                    <p class="card-text"><strong>ID:</strong> {game.id}</p>
                    <p class="card-text">
                        <strong>Жанр:</strong> {escape(game.genre)}
                    </p>
                    <p class="card-text">
                        <strong>Платформа:</strong> {escape(game.platform)}
                    </p>
                    <p class="card-text">
                        <strong>Год выпуска:</strong> {game.release_year}
                        <span class="badge bg-info text-dark">
                            {game.era()}
                        </span>
                    </p>
                    <p class="card-text">
                        <strong>Время прохождения:</strong>
                        {game.hours_total:.0f} ч
                    </p>
                    <p class="card-text">
                        <strong>Оценка:</strong> {game.rating_label()}
                    </p>
                    <a href="{reverse('games')}"
                       class="btn btn-outline-secondary">
                        ← к списку игр
                    </a>
                </div>
            </div>
        </div>
        <div class="col-lg-7">
            <h2 class="h4">Прогресс игроков</h2>
            <ul class="list-group shadow-sm mb-4">{players}</ul>
            <h2 class="h4">Активные сессии</h2>
            <ul class="list-group shadow-sm">{history}</ul>
        </div>
    </div>
    """
    return HttpResponse(page(game.title, content))
