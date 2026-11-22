"""Тесты страниц приложения gamesessions."""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import resolve, reverse
from django.utils import timezone

from games.models import Game
from gamesessions import views
from gamesessions.forms import SESSION_CONFLICT
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
        with self.assertNumQueries(5):
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
        self.assertContains(response, '<option value="-date" selected>')
        self.assertEqual(
            [session.pk for session in response.context["sessions"]], [2, 1],
        )

    def test_session_detail_shows_linked_objects(self) -> None:
        """Карточка сессии показывает связанные игру и игрока."""
        with self.assertNumQueries(3):
            response = self.client.get("/sessions/1/")
        self.assertTemplateUsed(response, "gamesessions/session_detail.html")
        self.assertContains(
            response, "<title>Сессия №1 - Игровая библиотека</title>"
        )
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "ivan@example.com")
        url = Game.objects.get(pk=1).get_absolute_url()
        self.assertContains(response, f'href="{url}"')
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
        params = {
            "q": "witcher", "player": "1", "status": "active", "sort": "date",
        }
        response = self.client.get("/sessions/", params)
        self.assertContains(
            response,
            "?q=witcher&amp;player=1&amp;status=active&amp;sort=date"
            "&amp;page=2",
        )
        self.assertEqual(
            [session.session_date.day for session in response.context[
                "sessions"
            ]],
            [10, 12, 13, 14, 15],
        )
        response = self.client.get("/sessions/", {**params, "page": "2"})
        self.assertEqual(
            [session.session_date.day for session in response.context[
                "sessions"
            ]],
            [16],
        )

    def test_invalid_filters_and_page_fall_back(self) -> None:
        """Некорректные параметры заменяются значениями по умолчанию."""
        response = self.client.get("/sessions/", {
            "game": "text", "player": "-1", "date": "2026-02-30",
            "sort": "invalid", "page": "abc",
        })
        self.assertContains(response, "Всего сессий: 2")
        self.assertContains(response, 'id="id_date_error"')
        self.assertEqual(response.context["sessions"].number, 1)

    def test_active_session_is_unique_per_player_game_and_day(self) -> None:
        """Ограничение блокирует дубль только для активных сессий."""
        fields = {
            "player_id": 1, "game_id": 1, "session_date": date(2026, 9, 10),
            "hours": 1,
        }
        with self.assertRaises(IntegrityError), transaction.atomic():
            GameSession.objects.create(**fields)
        GameSession.objects.create(
            **fields, status=GameSession.Status.CANCELLED,
        )
        GameSession.objects.create(
            **fields, status=GameSession.Status.COMPLETED,
        )

    def test_completed_history_and_queryset(self) -> None:
        """Менеджер сохраняет историю и поддерживает составные выборки."""
        selected = date(2026, 9, 10)
        completed = GameSession.objects.create(
            player_id=1, game_id=1, session_date=selected, hours=2,
            status=GameSession.Status.COMPLETED,
        )
        self.assertEqual(GameSession.objects.count(), 3)
        self.assertEqual(GameSession.objects.cancelled().get().pk, 2)
        active = GameSession.objects.for_date(selected).active().get()
        self.assertEqual(active.pk, 1)
        self.assertEqual(GameSession.objects.completed().get(), completed)
        response = self.client.get("/sessions/", {"status": "completed"})
        self.assertContains(response, "session-status-completed")
        self.assertContains(response, "Всего сессий: 1")
        self.assertContains(self.client.get("/sessions/1/"), "6,5 из 100 ч")


class SessionFormTests(LibraryTestCase):
    """Ввод, редактирование и отмена сессий через веб-формы."""

    def setUp(self) -> None:
        self.create_url = reverse("gamesessions:create")
        self.today = timezone.localdate()
        self.data = {
            "player": 1, "game": 1, "session_date": self.today.isoformat(),
            "hours": 2.5,
        }

    def test_create_and_validate_session(self) -> None:
        """Начальная дата, обязательные поля и проверка даты и часов."""
        response = self.client.get(self.create_url)
        self.assertContains(response, f'value="{self.today.isoformat()}"')
        response = self.client.post(self.create_url, {})
        self.assertFormError(
            response.context["form"], "player", "Обязательное поле."
        )
        response = self.client.post(self.create_url, {
            **self.data,
            "session_date": (self.today - timedelta(days=1)).isoformat(),
            "hours": 0,
        })
        form = response.context["form"]
        self.assertFormError(
            form, "session_date", "Нельзя выбрать прошедшую дату.",
        )
        self.assertFormError(
            form, "hours", "Количество часов должно быть больше нуля.",
        )
        self.assertEqual(GameSession.objects.count(), 2)
        response = self.client.post(self.create_url, {
            **self.data, "status": GameSession.Status.COMPLETED,
        })
        created = GameSession.objects.active().for_date(self.today).get()
        self.assertRedirects(
            response, reverse("gamesessions:detail", args=[created.pk]),
        )
        self.assertEqual(created.hours, 2.5)

    def test_edit_excludes_current_session_and_rejects_conflict(self) -> None:
        """Проверить обновление исходной записи и конфликт с другой сессией."""
        original = GameSession.objects.get(pk=1)
        edit_url = reverse("gamesessions:edit", args=[original.pk])
        data = {**self.data, "session_date": original.session_date.isoformat()}
        self.assertContains(
            self.client.get(edit_url),
            f'value="{original.session_date.isoformat()}"',
        )
        self.assertRedirects(self.client.post(edit_url, data), "/sessions/1/")
        original.refresh_from_db()
        self.assertEqual(original.hours, 2.5)
        self.client.post(self.create_url, self.data)
        response = self.client.post(edit_url, self.data)
        self.assertFormError(response.context["form"], None, SESSION_CONFLICT)
        duplicate = self.client.post(self.create_url, self.data)
        self.assertFormError(duplicate.context["form"], None, SESSION_CONFLICT)
        original.refresh_from_db()
        self.assertEqual(
            original.session_date.isoformat(), data["session_date"],
        )
        self.assertEqual(GameSession.objects.count(), 3)
        self.assertEqual(
            self.client.get("/sessions/999/edit/").status_code, 404,
        )

    def test_cancel_frees_date_and_preserves_history(self) -> None:
        """Отмена требует POST с CSRF и исключает сессию из прогресса."""
        self.client.post(self.create_url, self.data)
        session = GameSession.objects.active().for_date(self.today).get()
        detail_url = reverse("gamesessions:detail", args=[session.pk])
        cancel_url = reverse("gamesessions:cancel", args=[session.pk])
        client = Client(enforce_csrf_checks=True)
        response = client.get(detail_url)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertEqual(client.get(cancel_url).status_code, 405)
        self.assertEqual(client.post(cancel_url).status_code, 403)
        token = client.cookies["csrftoken"].value
        self.assertRedirects(
            client.post(cancel_url, {"csrfmiddlewaretoken": token}),
            detail_url,
        )
        session.refresh_from_db()
        self.assertEqual(session.status, GameSession.Status.CANCELLED)
        self.assertContains(client.get(detail_url), "session-status-cancelled")
        self.assertEqual(self.client.post(cancel_url).status_code, 404)
        self.assertEqual(
            self.client.get(f"/sessions/{session.pk}/edit/").status_code, 404,
        )
        response = self.client.post(self.create_url, self.data)
        self.assertEqual(response.status_code, 302)


class LibraryAdminTests(LibraryTestCase):
    """Реальные страницы Django Admin на тестовой базе."""

    def setUp(self) -> None:
        admin_user = User.objects.create_superuser("test-admin")
        self.client.force_login(admin_user)

    def test_session_admin_search_and_status_filter(self) -> None:
        """Поиск работает по связанной игре и почте игрока."""
        url = reverse("admin:gamesessions_gamesession_changelist")
        response = self.client.get(
            url,
            {"q": "Witcher anna@example.com", "status__exact": "cancelled"},
        )
        self.assertEqual(response.status_code, 200)
        results = response.context["cl"].result_list
        self.assertEqual([session.pk for session in results], [2])

    def test_related_sessions_and_public_game_url(self) -> None:
        """В обеих админ-карточках видны связанные записи."""
        game_admin = reverse("admin:games_game_change", args=[1])
        player_admin = reverse("admin:gamesessions_player_change", args=[1])
        session_admin = reverse(
            "admin:gamesessions_gamesession_change", args=[1],
        )
        response = self.client.get(game_admin)
        self.assertContains(response, session_admin)
        public_link = response.context["absolute_url"]
        self.assertContains(response, f'href="{public_link}"')
        game = Game.objects.get(pk=1)
        self.assertRedirects(
            self.client.get(public_link),
            f"http://testserver{game.get_absolute_url()}",
        )
        self.assertContains(self.client.get(player_admin), session_admin)

    def test_bulk_cancel_skips_completed_sessions(self) -> None:
        """Административное действие меняет только активные сессии."""
        completed = GameSession.objects.create(
            player_id=1, game_id=1, session_date=date(2026, 9, 10), hours=1,
            status=GameSession.Status.COMPLETED,
        )
        response = self.client.post(
            reverse("admin:gamesessions_gamesession_changelist"),
            {
                "action": "cancel_sessions",
                "_selected_action": [1, completed.pk],
                "index": 0,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(GameSession.objects.active().exists())
        self.assertEqual(GameSession.objects.completed().get(), completed)
