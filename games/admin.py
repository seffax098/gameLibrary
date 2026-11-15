"""Панель администрирования приложения игр."""

from django.contrib import admin

from gamesessions.admin import GameSessionInline

from .models import Game


class SessionsForGameInline(GameSessionInline):
    """Сессии, связанные с редактируемой игрой."""

    fields = ("player", "session_date", "hours", "status")
    readonly_fields = ("player", "session_date", "status")


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Поиск, фильтры и редактирование каталога."""

    list_display = (
        "id", "title", "platform", "release_year", "hours_total", "is_long",
        "rating",
    )
    list_display_links = ("title",)
    list_editable = ("hours_total",)
    search_fields = ("title",)
    list_filter = ("platform", "genre", "is_long")
    ordering = ("title", "pk")
    list_per_page = 20
    readonly_fields = ("id", "slug", "is_long")
    inlines = (SessionsForGameInline,)
