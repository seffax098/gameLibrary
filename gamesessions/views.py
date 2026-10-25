"""View-функции приложения gamesessions."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.sessions import find_session_by_id, get_progress
from storage import load_library


def sessions(request: HttpRequest) -> HttpResponse:
    """Страница /sessions/: все сессии из data/sessions.json по датам."""
    _, _, sessions_list = load_library(settings.DATA_DIR)
    context = {
        "sessions": sorted(sessions_list, key=lambda item: item.date),
    }
    return render(request, "gamesessions/session_list.html", context)


def session_detail(
    request: HttpRequest,
    session_id: int,
) -> HttpResponse:
    """Страница /sessions/<id>/: карточка сессии и прогресс игрока."""
    _, _, sessions_list = load_library(settings.DATA_DIR)
    session = find_session_by_id(sessions_list, session_id)
    context: dict[str, object] = {"session": session}
    if session is not None:
        context["progress"] = get_progress(
            sessions_list, session.user, session.game
        )
    return render(
        request,
        "gamesessions/session_detail.html",
        context,
        status=404 if session is None else 200,
    )
