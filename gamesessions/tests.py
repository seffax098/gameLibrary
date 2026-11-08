"""Тесты страниц приложения gamesessions."""

from datetime import date

from django.db import IntegrityError, transaction
from django.urls import resolve, reverse

from gamesessions import views
from gamesessions.models import GameSession
from homepage.testing import LibraryTestCase


class SessionsPagesTests(LibraryTestCase):
    """Страницы /sessions/ и /sessions/<id>/."""

    def test_sessions_urls(self) -> None:
        """Адреса связаны с view-функциями, id передаётся числом."""
        self.assertEqual(reverse("gamesessions:list"), "/sessions/")
        self.assertEqual(
            reverse("gamesessions:detail", args=[2]), "/sessions/2/"
        )
        match = resolve("/sessions/2/")
        self.assertEqual(match.func, views.session_detail)
        self.assertEqual(match.namespace, "gamesessions")
        self.assertEqual(match.kwargs, {"session_id": 2})

    def test_sessions_list_shows_cancelled(self) -> None:
        """Список содержит и активные, и отменённые сессии."""
        response = self.client.get("/sessions/")
        self.assertTemplateUsed(response, "gamesessions/session_list.html")
        self.assertTemplateUsed(
            response, "gamesessions/includes/session_status.html"
        )
        self.assertContains(response, 'href="/sessions/1/"')
        self.assertContains(response, 'href="/sessions/2/"')
        self.assertContains(response, "session-status-active")
        self.assertContains(response, "session-status-cancelled")
        self.assertContains(response, "Всего сессий: 2")

    def test_session_detail_shows_linked_objects(self) -> None:
        """Карточка сессии показывает связанные игру и игрока."""
        response = self.client.get("/sessions/1/")
        self.assertTemplateUsed(response, "gamesessions/session_detail.html")
        self.assertContains(
            response, "<title>Сессия №1 - Игровая библиотека</title>"
        )
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "ivan@example.com")
        self.assertContains(response, 'href="/games/1/"')
        self.assertContains(response, "10.09.2026")
        self.assertContains(response, "4,5 из 100 ч")

    def test_unknown_session_returns_404(self) -> None:
        """Несуществующая сессия - страница ошибки с кодом 404."""
        response = self.client.get("/sessions/999/")
        self.assertContains(response, "Сессия не найдена", status_code=404)
        self.assertContains(response, 'href="/sessions/"', status_code=404)

    def test_search_and_filters_include_cancelled_history(self) -> None:
        """Поиск и фильтры сохраняют отменённые сессии в истории."""
        response = self.client.get("/sessions/", {
            "q": "смирнова", "game": "1", "player": "2", "date": "2026-09-11",
        })
        self.assertContains(response, 'href="/sessions/2/"')
        self.assertNotContains(response, 'href="/sessions/1/"')
        self.assertContains(response, "session-status-cancelled")

    def test_sort_and_page_preserve_search_and_filter(self) -> None:
        """Следующая страница сохраняет поиск, фильтр и порядок."""
        for day in range(12, 17):
            GameSession.objects.create(
                game_id=1, player_id=1, session_date=date(2026, 9, day),
                hours=1,
            )
        params = {"q": "witcher", "player": "1", "sort": "-date"}
        response = self.client.get("/sessions/", params)
        self.assertContains(
            response, '?q=witcher&amp;player=1&amp;sort=-date&amp;page=2'
        )
        self.assertEqual(
            [session.session_date.day for session in response.context[
                "sessions"
            ]],
            [16, 15, 14, 13, 12],
        )
        response = self.client.get("/sessions/", {**params, "page": "2"})
        self.assertContains(response, 'href="/sessions/1/"')
        self.assertNotContains(response, 'href="/sessions/2/"')

    def test_invalid_filters_and_page_fall_back(self) -> None:
        """Некорректные параметры заменяются значениями по умолчанию."""
        response = self.client.get("/sessions/", {
            "game": "text", "player": "-1", "date": "2026-02-30",
            "sort": "invalid", "page": "abc",
        })
        self.assertContains(response, "Всего сессий: 2")
        self.assertEqual(response.context["sessions"].number, 1)

    def test_active_session_is_unique_per_player_game_and_day(self) -> None:
        """Ограничение блокирует дубль только для активных сессий."""
        fields = {
            "player_id": 1, "game_id": 1, "session_date": date(2026, 9, 10),
            "hours": 1,
        }
        with self.assertRaises(IntegrityError), transaction.atomic():
            GameSession.objects.create(**fields)
        GameSession.objects.create(**fields, is_cancelled=True)
