"""Тесты страниц приложения gamesessions."""

from django.urls import resolve, reverse

from gamesessions import views
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
