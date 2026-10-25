"""Маршруты приложения gamesessions (префикс sessions/ задан в urls.py)."""

from django.urls import path

from . import views

app_name = "gamesessions"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.sessions, name="list"),
    path("<int:session_id>/", views.session_detail, name="detail"),
]
