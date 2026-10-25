"""Маршруты приложения games (префикс games/ задан в корневом urls.py)."""

from django.urls import path

from . import views

app_name = "games"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.games, name="list"),
    path("search/", views.game_search, name="search"),
    path("unplayed/", views.unplayed_games, name="unplayed"),
    path("<int:game_id>/", views.game_detail, name="detail"),
]
