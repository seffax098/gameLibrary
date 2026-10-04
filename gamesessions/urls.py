"""Маршруты приложения gamesessions (префикс sessions/ задан в urls.py)."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.sessions, name="sessions"),
    path("<int:session_id>/", views.session_detail, name="session_detail"),
]
