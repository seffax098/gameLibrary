"""Формы каталога игр."""

from django import forms

from games.models import Game


class GameForm(forms.ModelForm):
    """Добавление игры с необязательной обложкой."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Поля каталога, доступные при добавлении игры."""

        model = Game
        fields = (
            "title", "genre", "platform", "release_year", "hours_total",
            "rating", "cover",
        )
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "genre": forms.TextInput(attrs={"class": "form-control"}),
            "platform": forms.Select(attrs={"class": "form-select"}),
            "release_year": forms.NumberInput(attrs={"class": "form-control"}),
            "hours_total": forms.NumberInput(attrs={"class": "form-control"}),
            "rating": forms.NumberInput(attrs={"class": "form-control"}),
            "cover": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_hours_total(self) -> float:
        """Проверить положительное время прохождения."""
        hours_total = self.cleaned_data["hours_total"]
        if hours_total <= 0:
            raise forms.ValidationError(
                "Время прохождения должно быть больше нуля."
            )
        return hours_total


class AvailabilityDateForm(forms.Form):
    """Проверка необязательной даты в подборе игр."""

    date = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
