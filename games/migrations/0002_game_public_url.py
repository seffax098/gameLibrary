"""Добавление адресов и вычисляемого признака длительности игр."""

from django.db import migrations, models
from django.utils.text import slugify
from unidecode import unidecode


def populate_slugs(apps, schema_editor) -> None:
    """Дать существующим играм стабильные URL с уникальным суффиксом."""
    game_model = apps.get_model("games", "Game")
    games = game_model.objects.using(schema_editor.connection.alias)
    for game in games.only("pk", "title").iterator():
        suffix = str(game.pk)
        limit = 180 - len(suffix) - 1
        title_slug = slugify(unidecode(game.title))[:limit].rstrip("-_")
        slug = f"{title_slug or 'game'}-{suffix}"
        games.filter(pk=game.pk).update(slug=slug)


class Migration(migrations.Migration):
    """Сначала заполнить слаги, затем потребовать их уникальность."""

    dependencies = [("games", "0001_initial")]
    operations = [
        migrations.AlterModelOptions(
            name="game",
            options={"verbose_name": "игра", "verbose_name_plural": "Игры"},
        ),
        migrations.AddField(
            model_name="game",
            name="slug",
            field=models.SlugField(
                "URL-идентификатор", max_length=180, null=True, editable=False,
            ),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="game",
            name="slug",
            field=models.SlugField(
                "URL-идентификатор", max_length=180, unique=True,
                editable=False,
            ),
        ),
        migrations.AddField(
            model_name="game",
            name="is_long",
            field=models.GeneratedField(
                expression=models.Case(
                    models.When(hours_total__gte=50, then=True),
                    default=False,
                ),
                output_field=models.BooleanField(),
                db_persist=True,
                verbose_name="длительная игра",
            ),
        ),
    ]
