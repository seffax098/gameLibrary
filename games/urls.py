"""Маршруты приложения games (префикс games/ задан в корневом urls.py)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.games, name="games"),
    path("<int:game_id>/", views.game_detail, name="game_detail"),
]
