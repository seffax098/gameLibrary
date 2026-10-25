"""Тесты страниц приложения games."""

from django.urls import resolve, reverse

from games import views
from homepage.testing import LibraryTestCase


class GamesPagesTests(LibraryTestCase):
    """Страницы /games/ и /games/<id>/."""

    def test_games_urls(self) -> None:
        """Адреса связаны с view-функциями, id передаётся числом."""
        self.assertEqual(reverse("games:list"), "/games/")
        self.assertEqual(reverse("games:detail", args=[1]), "/games/1/")
        match = resolve("/games/1/")
        self.assertEqual(match.func, views.game_detail)
        self.assertEqual(match.namespace, "games")
        self.assertEqual(match.kwargs, {"game_id": 1})

    def test_games_list(self) -> None:
        """Список показывает игры со ссылками на их страницы."""
        response = self.client.get("/games/")
        self.assertTemplateUsed(response, "games/game_list.html")
        self.assertTemplateUsed(response, "games/includes/game_row.html")
        self.assertContains(response, "<title>Игры - Игровая библиотека")
        self.assertContains(response, "The Witcher 3")
        self.assertContains(response, 'href="/games/1/"')
        self.assertContains(response, "10/10 - шедевр")
        self.assertContains(response, "Всего игр: 2")

    def test_games_list_passes_context(self) -> None:
        """Контекст содержит строки базы: поля доступны по именам."""
        response = self.client.get("/games/")
        witcher, classic = response.context["games"]
        self.assertEqual(witcher["title"], "The Witcher 3")
        self.assertEqual(witcher["played"], 4.5)
        self.assertEqual(classic["played"], 0)
        self.assertIsNone(classic["rating"])

    def test_games_list_links_to_search_pages(self) -> None:
        """Со страницы списка можно перейти к поиску и подбору игр."""
        response = self.client.get("/games/")
        self.assertContains(response, 'href="/games/search/"')
        self.assertContains(response, 'href="/games/unplayed/"')
        self.assertContains(response, "не выставлена")

    def test_games_list_escapes_titles(self) -> None:
        """Название игры выводится как текст, а не как разметка."""
        response = self.client.get("/games/")
        self.assertContains(response, "Tom &amp; Jerry &lt;Classic&gt;")
        self.assertNotContains(response, "<Classic>")

    def test_game_detail(self) -> None:
        """Карточка игры показывает её данные и прогресс игроков."""
        response = self.client.get("/games/1/")
        self.assertTemplateUsed(response, "games/game_detail.html")
        self.assertTemplateUsed(response, "games/includes/progress.html")
        self.assertContains(
            response, "<title>The Witcher 3 - Игровая библиотека</title>"
        )
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "4,5 из 100 ч")
        self.assertContains(response, 'href="/sessions/1/"')
        self.assertContains(response, "10.09.2026")

    def test_cancelled_session_is_not_in_progress(self) -> None:
        """Отменённая сессия Анны не даёт ей прогресса."""
        response = self.client.get("/games/1/")
        self.assertContains(response, "0,0 из 100 ч")
        self.assertNotContains(response, 'href="/sessions/2/"')

    def test_game_without_sessions(self) -> None:
        """Для игры без сессий срабатывает ветка {% empty %}."""
        response = self.client.get("/games/2/")
        self.assertContains(response, "Сессий пока нет")

    def test_unknown_game_returns_404(self) -> None:
        """Несуществующая игра - страница ошибки с кодом 404."""
        response = self.client.get("/games/999/")
        self.assertTemplateUsed(response, "games/game_detail.html")
        self.assertContains(response, "Игра не найдена", status_code=404)
        self.assertContains(response, 'href="/games/"', status_code=404)

    def test_non_numeric_id_is_not_routed(self) -> None:
        """Конвертер int не пропускает нечисловой идентификатор."""
        response = self.client.get("/games/witcher/")
        self.assertEqual(response.status_code, 404)


class GameSearchTests(LibraryTestCase):
    """Страница /games/search/: поиск игр по условиям."""

    def test_search_url(self) -> None:
        """Адрес поиска связан с view-функцией game_search()."""
        self.assertEqual(reverse("games:search"), "/games/search/")
        self.assertEqual(resolve("/games/search/").func, views.game_search)

    def test_search_without_conditions_shows_all_games(self) -> None:
        """Без условий найдены все игры, в списке - платформы базы."""
        response = self.client.get("/games/search/")
        self.assertTemplateUsed(response, "games/game_search.html")
        self.assertContains(response, "Найдено игр: 2")
        self.assertEqual(response.context["platforms"], ["PC"])

    def test_search_by_year(self) -> None:
        """Условие на год выпуска отбирает игры через WHERE."""
        response = self.client.get("/games/search/", {"year_from": 2010})
        titles = [row["title"] for row in response.context["games"]]
        self.assertEqual(titles, ["The Witcher 3"])

    def test_search_by_rating_treats_null_as_zero(self) -> None:
        """Игра без оценки (NULL) проходит только условие «не ниже 0»."""
        response = self.client.get("/games/search/", {"rating_from": 0})
        self.assertEqual(len(response.context["games"]), 2)
        response = self.client.get("/games/search/", {"rating_from": 5})
        self.assertEqual(len(response.context["games"]), 1)

    def test_search_value_is_passed_as_parameter(self) -> None:
        """Значение из формы не меняет текст SQL-запроса."""
        response = self.client.get(
            "/games/search/", {"platform": "' OR 1=1 --"}
        )
        self.assertContains(response, "Игр с такими условиями нет.")

    def test_search_ignores_wrong_numbers(self) -> None:
        """Нечисловой год не вызывает ошибку: условие не применяется."""
        response = self.client.get("/games/search/", {"year_from": "abc"})
        self.assertContains(response, "Найдено игр: 2")
        self.assertContains(response, 'value="abc"')


class UnplayedGamesTests(LibraryTestCase):
    """Страница /games/unplayed/: игры, в которые игрок не играл."""

    def test_unplayed_url(self) -> None:
        """Адрес связан с view-функцией unplayed_games()."""
        self.assertEqual(reverse("games:unplayed"), "/games/unplayed/")
        self.assertEqual(
            resolve("/games/unplayed/").func, views.unplayed_games
        )

    def test_without_player_shows_only_form(self) -> None:
        """Пока игрок не выбран, запрос к играм не выполняется."""
        response = self.client.get("/games/unplayed/")
        self.assertTemplateUsed(response, "games/game_unplayed.html")
        self.assertIsNone(response.context["player"])
        self.assertContains(response, "Анна Смирнова")
        self.assertNotContains(response, "ещё не играл")

    def test_played_game_is_excluded(self) -> None:
        """Игра с активной сессией игрока исключается подзапросом."""
        response = self.client.get("/games/unplayed/", {"user": 1})
        titles = [row["title"] for row in response.context["games"]]
        self.assertEqual(titles, ["Tom & Jerry <Classic>"])
        self.assertContains(response, "Иван Петров ещё не играл(а)")

    def test_cancelled_session_does_not_count(self) -> None:
        """У Анны сессия по игре отменена - игра остаётся в списке."""
        response = self.client.get("/games/unplayed/", {"user": 2})
        self.assertEqual(len(response.context["games"]), 2)

    def test_unknown_player(self) -> None:
        """Несуществующий игрок не выбирается."""
        response = self.client.get("/games/unplayed/", {"user": 999})
        self.assertIsNone(response.context["player"])
        self.assertEqual(response.context["games"], [])
