"""Тесты главной страницы и общего каркаса страниц."""

from django.urls import resolve, reverse

from gamelibrary import urls as gamelibrary_urls
from homepage import views
from homepage.testing import LibraryTestCase


class IndexPageTests(LibraryTestCase):
    """Страница / и функция page()."""

    def test_index_url(self) -> None:
        """Адрес / обрабатывается view-функцией index()."""
        self.assertEqual(reverse("index"), "/")
        self.assertEqual(resolve("/").func, views.index)

    def test_index_page(self) -> None:
        """Главная страница показывает описание и сводку библиотеки."""
        response = self.client.get("/")
        self.assertContains(response, "<title>Игровая библиотека</title>")
        self.assertContains(response, "Игр в библиотеке")
        self.assertContains(response, "Популярные игры")
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "4.5 ч")

    def test_page_has_bootstrap_and_navigation(self) -> None:
        """Каркас подключает Bootstrap и ссылки на все разделы."""
        html = views.page("Заголовок", "<p>Текст</p>")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn(views.BOOTSTRAP_CSS, html)
        self.assertIn('name="viewport"', html)
        for name in ("index", "games", "sessions"):
            self.assertIn(f'href="{reverse(name)}"', html)
        self.assertIn('<main class="container py-5"><p>Текст</p>', html)

    def test_page_marks_active_section(self) -> None:
        """Текущий раздел выделяется в навигации, остальные - нет."""
        html = views.page("Игры", "", active="games")
        self.assertIn(
            f'class="nav-link active" aria-current="page" '
            f'href="{reverse("games")}"',
            html,
        )
        self.assertEqual(html.count('aria-current="page"'), 1)

    def test_page_escapes_title(self) -> None:
        """Заголовок вкладки экранируется."""
        html = views.page("<b>Игра</b>", "")
        self.assertIn("<title>&lt;b&gt;Игра&lt;/b&gt;</title>", html)

    def test_unknown_url_shows_custom_404(self) -> None:
        """Адрес без маршрута - собственная страница 404 проекта.

        Тесты Django выполняются с DEBUG = False, поэтому срабатывает
        обработчик handler404, а не отладочная страница.
        """
        response = self.client.get("/nonexistent/")
        self.assertContains(response, "Страница не найдена", status_code=404)
        self.assertContains(response, views.BOOTSTRAP_CSS, status_code=404)
        self.assertContains(response, 'href="/"', status_code=404)

    def test_handler404_is_configured(self) -> None:
        """handler404 объявлен в корневом urls.py."""
        self.assertEqual(
            gamelibrary_urls.handler404, "homepage.views.page_not_found"
        )

    def test_not_found_returns_404(self) -> None:
        """not_found() возвращает страницу ошибки с кодом 404."""
        response = views.not_found("Нет такой страницы", "/", "← назад")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Нет такой страницы", response.content.decode())
