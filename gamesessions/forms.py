"""Формы поиска и записи игровых сессий."""

from datetime import date

from django import forms
from django.utils import timezone

from games.models import Game
from gamesessions.models import GameSession, Player


DEFAULT_SESSION_SORT = "-date"
SESSION_ORDER = {
    DEFAULT_SESSION_SORT: ("Дата ↓", "-session_date"),
    "date": ("Дата ↑", "session_date"),
    "game": ("Игра", "game__title"),
    "player": ("Игрок", "player__name"),
    "-hours": ("Сыгранные часы ↓", "-hours"),
}
SESSION_CONFLICT = (
    "У игрока уже есть активная сессия по этой игре на эту дату."
)
DATE_WIDGET = forms.DateInput(
    format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"},
)


class SessionFilters(forms.Form):
    """Проверка параметров поиска, фильтрации и сортировки."""

    q = forms.CharField(
        label="Название игры или имя игрока", required=False, max_length=255,
        widget=forms.TextInput(
            attrs={"type": "search", "class": "form-control"}
        ),
    )
    game = forms.ModelChoiceField(
        label="Игра", required=False, empty_label="Любая",
        queryset=Game.objects.order_by("title", "pk"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    player = forms.ModelChoiceField(
        label="Игрок", required=False, empty_label="Любой",
        queryset=Player.objects.order_by("name", "pk"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    date = forms.DateField(
        label="Дата сессии", required=False, input_formats=["%Y-%m-%d"],
        widget=DATE_WIDGET,
    )
    status = forms.ChoiceField(
        label="Статус", required=False,
        choices=[("", "Любой"), *GameSession.Status.choices],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sort = forms.ChoiceField(
        label="Сортировка", required=False, initial=DEFAULT_SESSION_SORT,
        choices=[(key, label) for key, (label, _) in SESSION_ORDER.items()],
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class GameSessionForm(forms.ModelForm):
    """Создание или редактирование активной сессии."""

    session_date = forms.DateField(
        label="Дата сессии", input_formats=["%Y-%m-%d"], widget=DATE_WIDGET,
        help_text="Для новой сессии выберите текущую или более позднюю дату.",
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Поля сессии, доступные пользователю."""

        model = GameSession
        fields = ("player", "game", "session_date", "hours")
        widgets = {
            "player": forms.Select(attrs={"class": "form-select"}),
            "game": forms.Select(attrs={"class": "form-select"}),
            "hours": forms.NumberInput(attrs={"class": "form-control"}),
        }
        help_texts = {"hours": "Укажите положительное количество часов."}

    def clean_session_date(self) -> date:
        """Не назначать новую дату в прошлом, сохраняя прежние записи."""
        session_date = self.cleaned_data["session_date"]
        if (
            session_date != self.instance.session_date
            and session_date < timezone.localdate()
        ):
            raise forms.ValidationError("Нельзя выбрать прошедшую дату.")
        return session_date

    def clean_hours(self) -> float:
        """Проверить, что продолжительность больше нуля."""
        hours = self.cleaned_data["hours"]
        if hours <= 0:
            raise forms.ValidationError(
                "Количество часов должно быть больше нуля."
            )
        return hours

    def clean(self) -> dict:
        """Проверить доступность выбранной игры для игрока на эту дату."""
        cleaned_data = super().clean() or {}
        if (
            cleaned_data.get("player") and cleaned_data.get("game")
            and cleaned_data.get("session_date") and self.has_conflict()
        ):
            raise forms.ValidationError(SESSION_CONFLICT)
        return cleaned_data

    def has_conflict(self) -> bool:
        """Проверить, есть ли другая активная сессия на выбранную дату."""
        return GameSession.objects.active().for_date(
            self.cleaned_data["session_date"]
        ).filter(
            player=self.cleaned_data["player"], game=self.cleaned_data["game"],
        ).exclude(pk=self.instance.pk).exists()
