"""Фильтры шаблонов для данных игр из базы SQLite."""

from django import template

from models.games import describe_rating

register = template.Library()


@register.filter
def rating_label(rating: int | None) -> str:
    """Описание оценки: {{ game.rating|rating_label }}."""
    return describe_rating(rating)
