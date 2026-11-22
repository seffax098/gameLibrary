"""Переход с признака отмены на три статуса игровых сессий."""

from django.db import migrations, models


def populate_statuses(apps, schema_editor) -> None:
    """Преобразовать старый признак отмены без удаления сессий."""
    session_model = apps.get_model("gamesessions", "GameSession")
    sessions = session_model.objects.using(schema_editor.connection.alias)
    sessions.filter(is_cancelled=True).update(status="cancelled")


def restore_cancelled_flag(apps, schema_editor) -> None:
    """В старой схеме пометить неактивные сессии как отменённые."""
    session_model = apps.get_model("gamesessions", "GameSession")
    sessions = session_model.objects.using(schema_editor.connection.alias)
    sessions.exclude(status="active").update(is_cancelled=True)


class Migration(migrations.Migration):
    """Перенести данные перед удалением старого поля."""

    dependencies = [("gamesessions", "0001_initial")]
    operations = [
        migrations.AlterModelOptions(
            name="player",
            options={"verbose_name": "игрок", "verbose_name_plural": "Игроки"},
        ),
        migrations.AlterModelOptions(
            name="gamesession",
            options={
                "verbose_name": "игровая сессия",
                "verbose_name_plural": "Игровые сессии",
            },
        ),
        migrations.AlterField(
            model_name="gamesession",
            name="player",
            field=models.ForeignKey(
                on_delete=models.CASCADE, related_name="sessions",
                to="gamesessions.player", verbose_name="игрок",
            ),
        ),
        migrations.AlterField(
            model_name="gamesession",
            name="game",
            field=models.ForeignKey(
                on_delete=models.CASCADE, related_name="sessions",
                to="games.game", verbose_name="игра",
            ),
        ),
        migrations.AddField(
            model_name="gamesession",
            name="status",
            field=models.CharField(
                "статус", max_length=9, default="active",
                choices=[
                    ("active", "активна"), ("cancelled", "отменена"),
                    ("completed", "завершена"),
                ],
            ),
        ),
        migrations.RemoveConstraint(
            model_name="gamesession", name="unique_active_session_per_day",
        ),
        migrations.RunPython(populate_statuses, restore_cancelled_flag),
        migrations.RemoveField(model_name="gamesession", name="is_cancelled"),
        migrations.AddConstraint(
            model_name="gamesession",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="active"),
                fields=("player", "game", "session_date"),
                name="unique_active_session_per_day",
            ),
        ),
        migrations.AddConstraint(
            model_name="gamesession",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    status__in=("active", "cancelled", "completed")
                ),
                name="game_session_valid_status",
            ),
        ),
    ]
