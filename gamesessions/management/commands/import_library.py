"""Перенос библиотеки из базы ПР7 в таблицы Django."""

import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from games.models import Game
from gamesessions.models import GameSession, Player


class Command(BaseCommand):
    """Перенести записи с сохранением идентификаторов и связей."""

    help = "Перенести игры, игроков и сессии из базы ПР7 в Django ORM."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--source", type=Path, default=settings.LIBRARY_DB)

    def handle(self, *args, **options) -> None:
        source = options["source"].resolve()
        if not source.is_file():
            raise CommandError(f"Исходная база не найдена: {source}")

        try:
            uri = f"{source.as_uri()}?mode=ro"
            with closing(sqlite3.connect(uri, uri=True)) as db:
                db.row_factory = sqlite3.Row
                db.execute("BEGIN")
                with transaction.atomic():
                    games, players, sessions = self.import_rows(db)
        except (sqlite3.Error, DatabaseError, ValueError) as error:
            raise CommandError(f"Перенос отменён: {error}") from error

        self.stdout.write(self.style.SUCCESS(
            f"Перенесено игр: {games}, игроков: {players}, сессий: {sessions}."
        ))

    @staticmethod
    def import_rows(db: sqlite3.Connection) -> tuple[int, int, int]:
        """Сохранить игры и игроков перед их игровыми сессиями."""
        games = db.execute(
            "SELECT id, title, genre, platform, release_year, hours_total, "
            "rating FROM games ORDER BY id"
        ).fetchall()
        players = db.execute(
            "SELECT id, name, email FROM users ORDER BY id"
        ).fetchall()
        sessions = db.execute(
            "SELECT id, user_id, game_id, session_date, hours, is_cancelled "
            "FROM sessions ORDER BY id"
        ).fetchall()
        for row in games:
            fields = dict(row)
            pk = fields.pop("id")
            fields["rating"] = fields["rating"] or None
            Game.objects.update_or_create(pk=pk, defaults=fields)
        for row in players:
            Player.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"], "email": row["email"]},
            )
        for row in sessions:
            GameSession.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "player_id": row["user_id"],
                    "game_id": row["game_id"],
                    "session_date": date.fromisoformat(row["session_date"]),
                    "hours": row["hours"],
                    "is_cancelled": bool(row["is_cancelled"]),
                },
            )
        return len(games), len(players), len(sessions)
