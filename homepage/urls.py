"""Маршруты приложения homepage."""

from django.urls import path

from . import views

app_name = "homepage"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.index, name="index"),
    path("statistics/", views.statistics, name="statistics"),
]
