"""Тесты страниц приложения games."""

from django.urls import resolve, reverse

from games import views
from homepage.testing import LibraryTestCase


class GamesPagesTests(LibraryTestCase):
    """Страницы /games/ и /games/<id>/."""

    def test_games_urls(self) -> None:
        """Адреса связаны с view-функциями, id передаётся числом."""
        self.assertEqual(reverse("games"), "/games/")
        self.assertEqual(reverse("game_detail", args=[1]), "/games/1/")
        match = resolve("/games/1/")
        self.assertEqual(match.func, views.game_detail)
        self.assertEqual(match.kwargs, {"game_id": 1})

    def test_games_list(self) -> None:
        """Список показывает игры со ссылками на их страницы."""
        response = self.client.get("/games/")
        self.assertContains(response, "The Witcher 3")
        self.assertContains(response, 'href="/games/1/"')
        self.assertContains(response, "10/10 - шедевр")

    def test_games_list_escapes_titles(self) -> None:
        """Название игры выводится как текст, а не как разметка."""
        response = self.client.get("/games/")
        self.assertContains(response, "Tom &amp; Jerry &lt;Classic&gt;")
        self.assertNotContains(response, "<Classic>")

    def test_game_detail(self) -> None:
        """Карточка игры показывает её данные и прогресс игроков."""
        response = self.client.get("/games/1/")
        self.assertContains(response, "<title>The Witcher 3</title>")
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "4.5 из 100 ч")
        self.assertContains(response, 'href="/sessions/1/"')

    def test_cancelled_session_is_not_in_progress(self) -> None:
        """Отменённая сессия Анны не даёт ей прогресса."""
        response = self.client.get("/games/1/")
        self.assertContains(response, "0.0 из 100 ч")
        self.assertNotContains(response, 'href="/sessions/2/"')

    def test_unknown_game_returns_404(self) -> None:
        """Несуществующая игра - страница ошибки с кодом 404."""
        response = self.client.get("/games/999/")
        self.assertContains(response, "Игра не найдена", status_code=404)

    def test_non_numeric_id_is_not_routed(self) -> None:
        """Конвертер int не пропускает нечисловой идентификатор."""
        response = self.client.get("/games/witcher/")
        self.assertEqual(response.status_code, 404)
