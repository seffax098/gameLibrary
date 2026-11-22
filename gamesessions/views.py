"""Список и карточка игровых сессий."""

import re

from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from gamesessions.forms import (
    DEFAULT_SESSION_SORT,
    SESSION_CONFLICT, SESSION_ORDER, GameSessionForm, SessionFilters,
)
from gamesessions.models import GameSession
from models import Progress


def sessions(request: HttpRequest) -> HttpResponse:
    """История сессий с поиском, фильтрами и пагинацией."""
    form = SessionFilters(request.GET or None)
    # Применяем корректные фильтры, даже если другое поле содержит ошибку.
    form.full_clean()
    filters = form.cleaned_data if form.is_bound else {}
    sessions_list = GameSession.objects.select_related("player", "game")
    if query := filters.get("q"):
        pattern = re.escape(query)
        sessions_list = sessions_list.filter(
            Q(game__title__iregex=pattern) | Q(player__name__iregex=pattern)
        )
    if game := filters.get("game"):
        sessions_list = sessions_list.filter(game=game)
    if player := filters.get("player"):
        sessions_list = sessions_list.filter(player=player)
    if session_date := filters.get("date"):
        sessions_list = sessions_list.for_date(session_date)
    if status := filters.get("status"):
        sessions_list = sessions_list.filter(status=status)

    sort = filters.get("sort") or DEFAULT_SESSION_SORT
    sessions_list = sessions_list.order_by(SESSION_ORDER[sort][1], "pk")
    page = Paginator(sessions_list, 5).get_page(request.GET.get("page"))
    return render(request, "gamesessions/session_list.html", {
        "sessions": page, "form": form,
    })


@require_http_methods(["GET", "HEAD", "POST"])
def session_form(
    request: HttpRequest, session_id: int | None = None,
) -> HttpResponse:
    """Создать сессию или изменить существующую активную запись."""
    session = None
    if session_id is not None:
        session = get_object_or_404(
            GameSession.objects.active(), pk=session_id,
        )

    form = GameSessionForm(
        request.POST if request.method == "POST" else None,
        instance=session,
        initial={"session_date": timezone.localdate()}
        if session is None else None,
    )
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if session is None:
                    session = form.save()
                else:
                    # Не изменяем запись, если её успели отменить.
                    updated = GameSession.objects.active().filter(
                        pk=session.pk
                    ).update(**form.cleaned_data)
                    if not updated:
                        raise Http404
        except IntegrityError:
            if not form.has_conflict():
                raise
            form.add_error(None, SESSION_CONFLICT)
        else:
            return redirect("gamesessions:detail", session_id=session.pk)

    return render(request, "gamesessions/session_form.html", {
        "form": form, "session": session,
    })


@require_POST
def session_cancel(request: HttpRequest, session_id: int) -> HttpResponse:
    """Отменить активную сессию с сохранением её в истории."""
    session = get_object_or_404(GameSession.objects.active(), pk=session_id)
    if not session.cancel():
        raise Http404
    return redirect("gamesessions:detail", session_id=session.pk)


def session_detail(request: HttpRequest, session_id: int) -> HttpResponse:
    """Карточка сессии и прогресс игрока в связанной игре."""
    try:
        session = GameSession.objects.select_related("game", "player").get(
            pk=session_id
        )
    except GameSession.DoesNotExist:
        return render(
            request, "gamesessions/session_detail.html",
            {"session": None}, status=404,
        )

    totals = GameSession.objects.played().filter(
        player_id=session.player_id, game_id=session.game_id,
    ).aggregate(hours=Sum("hours", default=0))
    progress = Progress(
        session.player.as_library_user(),
        session.game.as_library_game(),
        totals["hours"],
    )
    return render(request, "gamesessions/session_detail.html", {
        "session": session, "progress": progress,
    })
