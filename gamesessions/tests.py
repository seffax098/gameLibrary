"""Тесты страниц приложения gamesessions."""

from django.test import SimpleTestCase
from django.urls import resolve, reverse

from gamesessions import views
from homepage.testing import LibraryDataMixin


class SessionsPagesTests(LibraryDataMixin, SimpleTestCase):
    """Страницы /sessions/ и /sessions/<id>/."""

    def test_sessions_urls(self):
        """Адреса связаны с view-функциями, id передаётся числом."""
        self.assertEqual(reverse("sessions"), "/sessions/")
        self.assertEqual(reverse("session_detail", args=[2]), "/sessions/2/")
        match = resolve("/sessions/2/")
        self.assertEqual(match.func, views.session_detail)
        self.assertEqual(match.kwargs, {"session_id": 2})

    def test_sessions_list_shows_cancelled(self):
        """Список содержит и активные, и отменённые сессии."""
        response = self.client.get("/sessions/")
        self.assertContains(response, 'href="/sessions/1/"')
        self.assertContains(response, 'href="/sessions/2/"')
        self.assertContains(response, "активна")
        self.assertContains(response, "отменена")

    def test_session_detail_shows_linked_objects(self):
        """Карточка сессии показывает связанные игру и игрока."""
        response = self.client.get("/sessions/1/")
        self.assertContains(response, "<title>Сессия №1</title>")
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "ivan@example.com")
        self.assertContains(response, 'href="/games/1/"')
        self.assertContains(response, "10.09.2026")

    def test_unknown_session_returns_404(self):
        """Несуществующая сессия - страница ошибки с кодом 404."""
        response = self.client.get("/sessions/999/")
        self.assertContains(response, "Сессия не найдена", status_code=404)
