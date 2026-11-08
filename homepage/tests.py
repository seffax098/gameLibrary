"""Тесты главной страницы, базового шаблона и страницы 404."""

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from gamelibrary import urls as gamelibrary_urls
from games.models import Game
from gamesessions.models import Player
from homepage import views
from homepage.testing import LibraryTestCase

BOOTSTRAP_CSS = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
)


class IndexPageTests(LibraryTestCase):
    """Страница / и базовый шаблон base.html."""

    def test_index_url(self) -> None:
        """Адрес / обрабатывается view-функцией index()."""
        self.assertEqual(reverse("homepage:index"), "/")
        self.assertEqual(resolve("/").func, views.index)

    def test_index_page(self) -> None:
        """Главная страница показывает описание и сводку библиотеки."""
        response = self.client.get("/")
        self.assertTemplateUsed(response, "homepage/index.html")
        self.assertContains(response, "<title>Игровая библиотека</title>")
        self.assertContains(response, "Игр в библиотеке")
        self.assertContains(response, "Популярные игры")
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "4,5 ч")
        summary = response.context["summary"]
        self.assertEqual(summary["games_count"], 2)
        self.assertEqual(summary["sessions_count"], 1)
        self.assertEqual(summary["cancelled_count"], 1)
        # AVG() не учитывает игру без оценки (NULL).
        self.assertEqual(summary["average_rating"], 10)

    def test_index_extends_base_template(self) -> None:
        """Главная наследует base.html и включает навигацию."""
        response = self.client.get("/")
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "includes/navigation.html")
        self.assertContains(response, "<!DOCTYPE html>")
        self.assertContains(response, 'name="viewport"')
        self.assertContains(response, BOOTSTRAP_CSS)

    def test_base_template_links_static_files(self) -> None:
        """Базовый шаблон подключает собственные CSS, JS и логотип."""
        response = self.client.get("/")
        self.assertContains(response, "/static/homepage/css/style.css")
        self.assertContains(response, "/static/homepage/js/main.js")
        self.assertContains(response, "/static/homepage/img/logo.png")
        self.assertContains(response, 'id="current-year"')

    def test_navigation_uses_named_urls(self) -> None:
        """Навигация ведёт во все разделы и выделяет текущий."""
        response = self.client.get(reverse("games:list"))
        for name in (
            "homepage:index",
            "games:list",
            "gamesessions:list",
            "homepage:statistics",
        ):
            self.assertContains(response, f'href="{reverse(name)}"')
        self.assertContains(response, 'aria-current="page"', count=1)
        self.assertContains(
            response,
            'class="nav-link active" aria-current="page"\n'
            f'                        href="{reverse("games:list")}"',
        )

    def test_unknown_url_shows_custom_404(self) -> None:
        """Адрес без маршрута - собственная страница 404 проекта."""
        response = self.client.get("/nonexistent/")
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Страница не найдена", status_code=404)
        self.assertContains(response, BOOTSTRAP_CSS, status_code=404)
        self.assertContains(response, 'href="/"', status_code=404)

    def test_empty_library(self) -> None:
        """Сводка работает на базе после миграций, до импорта."""
        Game.objects.all().delete()
        Player.objects.all().delete()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["games_count"], 0)
        self.assertEqual(response.context["summary"]["hours_played"], 0)

    def test_handler404_is_configured(self) -> None:
        """handler404 объявлен в корневом urls.py."""
        self.assertEqual(
            gamelibrary_urls.handler404, "homepage.views.page_not_found"
        )


class StatisticsPageTests(LibraryTestCase):
    """Страница /statistics/: агрегатные запросы и группировка."""

    def test_statistics_url(self) -> None:
        """Адрес связан с view-функцией statistics()."""
        self.assertEqual(reverse("homepage:statistics"), "/statistics/")
        self.assertEqual(resolve("/statistics/").func, views.statistics)

    def test_statistics_page(self) -> None:
        """Группы по жанрам, платформам и игрокам выводятся на странице."""
        response = self.client.get("/statistics/")
        self.assertTemplateUsed(response, "homepage/statistics.html")
        self.assertContains(response, "<title>Статистика - Игровая")
        self.assertContains(response, "Не указан")
        self.assertContains(response, "нет оценок")
        platforms = response.context["platforms"]
        self.assertEqual(len(platforms), 1)
        self.assertEqual(platforms[0]["games_count"], 2)
        self.assertEqual(platforms[0]["first_year"], 2001)

    def test_player_without_active_sessions_is_listed(self) -> None:
        """LEFT JOIN оставляет Анну: её единственная сессия отменена."""
        response = self.client.get("/statistics/")
        players = {row["name"]: row for row in response.context["players"]}
        self.assertEqual(players["Анна Смирнова"]["sessions_count"], 0)
        self.assertEqual(players["Анна Смирнова"]["hours"], 0)
        self.assertEqual(players["Иван Петров"]["hours"], 4.5)

    def test_having_threshold(self) -> None:
        """HAVING отбирает игры по сумме часов после группировки."""
        response = self.client.get("/statistics/")
        self.assertEqual(list(response.context["popular"]), [])
        self.assertContains(response, "Нет игр, в которые сыграно")
        response = self.client.get("/statistics/", {"min_hours": "4"})
        titles = [row["title"] for row in response.context["popular"]]
        self.assertEqual(titles, ["The Witcher 3"])

    def test_wrong_threshold_uses_default(self) -> None:
        """Нечисловой порог заменяется значением по умолчанию."""
        response = self.client.get("/statistics/", {"min_hours": "x"})
        self.assertEqual(response.context["min_hours"], 10.0)

    def test_statistics_is_active_in_navigation(self) -> None:
        """В меню выделен пункт «Статистика», а не «Главная»."""
        response = self.client.get("/statistics/")
        self.assertContains(response, 'aria-current="page"', count=1)
        self.assertContains(
            response,
            'class="nav-link active" aria-current="page"\n'
            '                        href="/statistics/"',
        )


class StaticFilesTests(SimpleTestCase):
    """Статические файлы приложения homepage."""

    def test_static_files_are_found(self) -> None:
        """Django находит CSS, JavaScript и логотип проекта."""
        for path in (
            "homepage/css/style.css",
            "homepage/js/main.js",
            "homepage/img/logo.png",
        ):
            self.assertIsNotNone(finders.find(path), path)
