"""Тесты главной страницы, базового шаблона и страницы 404."""

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from gamelibrary import urls as gamelibrary_urls
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
        self.assertEqual(response.context["stats"]["games"], 2)

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
        for name in ("homepage:index", "games:list", "gamesessions:list"):
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

    def test_handler404_is_configured(self) -> None:
        """handler404 объявлен в корневом urls.py."""
        self.assertEqual(
            gamelibrary_urls.handler404, "homepage.views.page_not_found"
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
