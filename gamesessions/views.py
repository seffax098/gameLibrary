"""View-функции приложения gamesessions.

Страницы строятся по объектам GameSession из JSON-хранилища ПР3.
Сессия связана с объектами User и Game, поэтому на странице доступны
данные игрока и игры: session.user.name, session.game.title.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from games.views import progress_html
from homepage.views import not_found, page, table_section
from models import GameSession
from models.sessions import DATE_FORMAT, find_session_by_id, get_progress
from storage import load_library


def status_badge(session: GameSession) -> str:
    """Вернуть бейдж состояния сессии по признаку is_cancelled."""
    if session.is_cancelled:
        return '<span class="badge bg-secondary">отменена</span>'
    return '<span class="badge bg-success">активна</span>'


def sessions(request: HttpRequest) -> HttpResponse:
    """Страница /sessions/: все сессии из data/sessions.json по датам.

    Отменённые сессии тоже показываются: они остаются в истории.
    """
    _, _, sessions_list = load_library(settings.DATA_DIR)
    rows = ""
    for session in sorted(sessions_list, key=lambda item: item.date):
        game_url = reverse("game_detail", args=[session.game.id])
        rows += f"""
        <tr>
            <td>
                <a href="{reverse('session_detail', args=[session.id])}">
                    №{session.id}
                </a>
            </td>
            <td>{session.date.strftime(DATE_FORMAT)}</td>
            <td>{escape(session.user.name)}</td>
            <td><a href="{game_url}">{escape(session.game.title)}</a></td>
            <td class="text-end">{session.hours:.1f} ч</td>
            <td>{status_badge(session)}</td>
        </tr>
        """
    header = (
        "<th>Сессия</th><th>Дата</th><th>Игрок</th><th>Игра</th>"
        '<th class="text-end">Часы</th><th>Статус</th>'
    )
    content = table_section("Игровые сессии", header, rows)
    return HttpResponse(page("Игровая библиотека - сессии", content))


def session_detail(
    request: HttpRequest,
    session_id: int,
) -> HttpResponse:
    """Страница /sessions/<id>/: карточка сессии и прогресс игрока.

    Если сессии с таким идентификатором нет, возвращается код 404.
    """
    _, _, sessions_list = load_library(settings.DATA_DIR)
    session = find_session_by_id(sessions_list, session_id)
    if session is None:
        return not_found(
            "Сессия не найдена", reverse("sessions"), "← к списку сессий"
        )

    progress = get_progress(sessions_list, session.user, session.game)
    game_url = reverse("game_detail", args=[session.game.id])
    content = f"""
    <div class="row g-4">
        <div class="col-lg-6">
            <div class="card shadow-sm">
                <div class="card-body">
                    <h1 class="h3 card-title">Сессия №{session.id}</h1>
                    <p class="card-text">
                        <strong>Игра:</strong>
                        <a href="{game_url}">
                            {escape(session.game.title)}
                        </a>
                    </p>
                    <p class="card-text">
                        <strong>Игрок:</strong>
                        {escape(session.user.name)}
                        ({escape(session.user.email)})
                    </p>
                    <p class="card-text">
                        <strong>Дата:</strong>
                        {session.date.strftime(DATE_FORMAT)}
                    </p>
                    <p class="card-text">
                        <strong>Сыграно:</strong> {session.hours:.1f} ч
                    </p>
                    <p class="card-text">
                        <strong>Статус:</strong> {status_badge(session)}
                    </p>
                    <a href="{reverse('sessions')}"
                       class="btn btn-outline-secondary">
                        ← к списку сессий
                    </a>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <h2 class="h4">Прогресс игрока в игре</h2>
            <div class="card shadow-sm">
                <div class="card-body">
                    {progress_html(progress)}
                    <p class="text-muted small mt-3 mb-0">
                        Прогресс считается по активным сессиям игрока:
                        отменённая сессия в нём не учитывается.
                    </p>
                </div>
            </div>
        </div>
    </div>
    """
    return HttpResponse(page(f"Сессия №{session.id}", content))
