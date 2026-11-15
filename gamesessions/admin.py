"""Панель администрирования приложения игровых сессий."""

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import GameSession, Player


class GameSessionInline(admin.TabularInline):
    """Общие настройки встроенной истории сессий."""

    model = GameSession
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ("-session_date", "-pk")

    def get_queryset(self, request: HttpRequest) -> QuerySet[GameSession]:
        """Загрузить игру и игрока вместе с каждой строкой истории."""
        return super().get_queryset(request).select_related("game", "player")

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        """Создавать сессии через их отдельную форму."""
        return False


class SessionsForPlayerInline(GameSessionInline):
    """Сессии, связанные с редактируемым игроком."""

    fields = ("game", "session_date", "hours", "status")
    readonly_fields = ("game", "session_date", "status")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Управление игроками и просмотр их истории."""

    list_display = ("id", "name", "email")
    list_display_links = ("name",)
    search_fields = ("name", "email")
    ordering = ("name", "pk")
    list_per_page = 20
    readonly_fields = ("id",)
    inlines = (SessionsForPlayerInline,)


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """Управление историей сессий и их статусами."""

    list_display = ("id", "game", "player", "session_date", "hours", "status")
    list_display_links = ("id",)
    search_fields = ("game__title", "player__name", "player__email")
    list_filter = ("status", "session_date", "game__platform")
    ordering = ("-session_date", "-pk")
    list_per_page = 20
    readonly_fields = ("id",)
    list_select_related = ("game", "player")
    autocomplete_fields = ("game", "player")
    date_hierarchy = "session_date"
    actions = ("cancel_sessions",)

    @admin.action(description="Отменить выбранные активные сессии",
                  permissions=["change"])
    def cancel_sessions(
        self, request: HttpRequest, queryset: QuerySet[GameSession],
    ) -> None:
        """Отменить только активные записи из выделенных."""
        count = queryset.filter(status=GameSession.Status.ACTIVE).update(
            status=GameSession.Status.CANCELLED
        )
        self.message_user(
            request, f"Отменено сессий: {count}.", messages.SUCCESS,
        )
