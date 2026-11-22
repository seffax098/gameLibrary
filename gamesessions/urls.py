"""Маршруты приложения gamesessions (префикс sessions/ задан в urls.py)."""

from django.urls import path

from . import views

app_name = "gamesessions"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.sessions, name="list"),
    path("add/", views.session_form, name="create"),
    path("<int:session_id>/", views.session_detail, name="detail"),
    path("<int:session_id>/edit/", views.session_form, name="edit"),
    path("<int:session_id>/cancel/", views.session_cancel, name="cancel"),
]
