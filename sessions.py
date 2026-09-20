"""Функции для работы с игровыми сессиями и прогрессом прохождения.

Сессии хранятся в списке ``sessions``: каждый элемент - словарь с
идентификатором сессии, идентификатором игры, датой и количеством
сыгранных часов.
"""

from datetime import date

PROGRESS_BAR_LENGTH: int = 10
FULL_PROGRESS: float = 100.0


def next_session_id(sessions: list[dict]) -> int:
    """Вернуть свободный идентификатор для новой сессии."""
    if not sessions:
        return 1
    return max(session["id"] for session in sessions) + 1


def is_day_free(
    sessions: list[dict],
    game_id: int,
    session_date: date,
) -> bool:
    """Проверить, свободен ли день для записи сессии по игре.

    Возвращает False, если сессия по этой игре на указанную дату
    уже записана.
    """
    for session in sessions:
        if session["game_id"] == game_id:
            if session["date"] == session_date:
                return False
    return True


def log_session(
    sessions: list[dict],
    game_id: int,
    session_date: date,
    hours: float,
) -> dict:
    """Записать игровую сессию и вернуть её данные.

    Повторная запись сессии по одной игре на ту же дату запрещена:
    в этом случае возбуждается исключение ValueError.
    """
    if hours <= 0:
        raise ValueError("Количество часов должно быть больше нуля.")
    if not is_day_free(sessions, game_id, session_date):
        raise ValueError(
            "Сессия по этой игре на указанную дату уже записана."
        )
    session = {
        "id": next_session_id(sessions),
        "game_id": game_id,
        "date": session_date,
        "hours": float(hours),
    }
    sessions.append(session)
    return session


def cancel_session(sessions: list[dict], session_id: int) -> dict:
    """Отменить сессию по идентификатору и вернуть её данные."""
    for index, session in enumerate(sessions):
        if session["id"] == session_id:
            return sessions.pop(index)
    raise KeyError(f"Сессия с идентификатором {session_id} не найдена.")


def cancel_game_sessions(sessions: list[dict], game_id: int) -> int:
    """Удалить все сессии игры и вернуть количество удалённых."""
    remaining = [
        session for session in sessions if session["game_id"] != game_id
    ]
    removed = len(sessions) - len(remaining)
    sessions[:] = remaining
    return removed


def game_sessions(sessions: list[dict], game_id: int) -> list[dict]:
    """Вернуть сессии выбранной игры, упорядоченные по дате."""
    selected = (
        session for session in sessions if session["game_id"] == game_id
    )
    return sorted(selected, key=lambda session: session["date"])


def hours_played(sessions: list[dict], game_id: int) -> float:
    """Подсчитать суммарное время, сыгранное в игру."""
    return sum(
        session["hours"]
        for session in sessions
        if session["game_id"] == game_id
    )


def calculate_progress(hours: float, hours_total: float) -> float:
    """Вычислить прогресс прохождения в процентах.

    Функция перенесена из первоначального сценария ПР1.
    """
    if hours_total <= 0:
        raise ValueError("Время прохождения должно быть больше нуля.")
    return min(hours / hours_total * FULL_PROGRESS, FULL_PROGRESS)


def get_status(hours: float, progress: float) -> str:
    """Вернуть статус прохождения игры.

    Функция перенесена из первоначального сценария ПР1.
    """
    if hours == 0:
        return "Не начата"
    if progress >= FULL_PROGRESS:
        return "Пройдена"
    return "В процессе"


def make_progress_bar(progress: float) -> str:
    """Построить текстовую шкалу прогресса.

    Функция перенесена из первоначального сценария ПР1.
    """
    filled = int(progress // PROGRESS_BAR_LENGTH)
    return "#" * filled + "-" * (PROGRESS_BAR_LENGTH - filled)


def get_game_progress(
    sessions: list[dict],
    game_id: int,
    hours_total: float,
) -> dict:
    """Собрать сведения о прогрессе прохождения игры."""
    hours = hours_played(sessions, game_id)
    progress = calculate_progress(hours, hours_total)
    return {
        "hours": hours,
        "hours_left": max(hours_total - hours, 0.0),
        "progress": progress,
        "status": get_status(hours, progress),
        "bar": make_progress_bar(progress),
    }
