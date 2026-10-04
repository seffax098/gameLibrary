"""Консольное приложение «Система управления игровой библиотекой».

Модуль содержит функции вывода данных, обработчики пунктов меню и
точку запуска программы. Классы предметной области (Game, User,
GameSession, Progress) и функции работы с их коллекциями находятся в
пакете models; статистика, хранение данных и безопасный ввод - в
модулях stats, storage и utils.
"""

import inspect
from collections.abc import Callable
from types import ModuleType

import stats as stats_module
import storage
import utils
from models import Game, GameSession, User
from models import games as games_module
from models import progress as progress_module
from models import sessions as sessions_module
from models import users as users_module

LINE_WIDTH: int = 60
MENU_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Игры", (
        "Показать библиотеку",
        "Найти игру по названию или жанру",
        "Отобрать игры по платформе",
        "Отсортировать игры",
        "Показать карточку игры",
        "Добавить игру",
        "Удалить игру",
    )),
    ("Пользователи", (
        "Показать пользователей",
        "Найти пользователя",
        "Показать профиль пользователя",
        "Добавить пользователя",
    )),
    ("Игровые сессии", (
        "Записать игровую сессию",
        "Отменить игровую сессию",
        "Показать игровые сессии",
    )),
    ("Сводка", (
        "Показать статистику библиотеки",
        "Справка по классам и функциям проекта",
    )),
)
MENU_ITEMS: tuple[str, ...] = tuple(
    item for _, items in MENU_SECTIONS for item in items
)
# Пункты меню, после которых данные нужно сохранить в файлы.
CHANGING_CHOICES: frozenset[int] = frozenset({6, 7, 11, 12, 13})
HELP_MODULES: tuple[ModuleType, ...] = (
    games_module,
    users_module,
    sessions_module,
    progress_module,
    stats_module,
    storage,
    utils,
)
HELP_DUNDERS: tuple[str, ...] = ("__init__", "__str__")


def print_title(text: str) -> None:
    """Вывести заголовок раздела."""
    print()
    print("=" * LINE_WIDTH)
    print(text.center(LINE_WIDTH))
    print("=" * LINE_WIDTH)


def show_games(games: list[Game], sessions: list[GameSession]) -> None:
    """Вывести список игр в виде таблицы."""
    if not games:
        print("Библиотека пуста: добавьте первую игру.")
        return
    print(
        f"{'ID':<4}{'Название':<26}{'Платформа':<16}"
        f"{'Год':<6}{'Сыграно':<8}"
    )
    print("-" * LINE_WIDTH)
    for game in games:
        hours = sessions_module.hours_played(sessions, game=game)
        print(
            f"{game.id:<4}{game.title[:25]:<26}"
            f"{game.platform:<16}{game.release_year:<6}"
            f"{hours:.1f} ч"
        )


def show_game_card(
    users: list[User],
    sessions: list[GameSession],
    game: Game,
) -> None:
    """Вывести подробную карточку игры с прогрессом каждого игрока.

    Карточка развивает вывод первоначального сценария ПР1: данные
    игры берутся из объекта Game, а прогресс - из сессий игроков.
    """
    players = [
        progress
        for progress in sessions_module.game_progress(sessions, users, game)
        if progress.hours
    ]
    played = len(sessions_module.active_sessions(sessions, game=game))

    print_title(f"Карточка игры: {game.title}")
    print(f"Жанр:              {game.genre}")
    print(f"Платформа:         {game.platform}")
    print(
        f"Год выпуска:       {game.release_year} "
        f"({game.era()}, лет с выхода: {game.age()})"
    )
    print(f"Время прохождения: {game.hours_total:.1f} ч")
    print(f"Оценка:            {game.rating_label()}")
    print(f"Сессий записано:   {played}")
    print("Прогресс игроков:")
    if not players:
        print("  в игру ещё никто не играл")
    for progress in players:
        print(
            f"  {progress.user.name[:19]:<20}{progress}, "
            f"{progress.hours:.1f} ч"
        )
    print("=" * LINE_WIDTH)


def show_users(users: list[User], sessions: list[GameSession]) -> None:
    """Вывести список пользователей с их игровым временем."""
    if not users:
        print("Пользователей нет: добавьте первого пользователя.")
        return
    print(f"{'ID':<4}{'Пользователь':<46}{'Сыграно':<10}")
    print("-" * LINE_WIDTH)
    for user in users:
        hours = sessions_module.hours_played(sessions, user=user)
        print(f"{user.id:<4}{str(user)[:45]:<46}{hours:.1f} ч")


def show_user_profile(
    games: list[Game],
    sessions: list[GameSession],
    user: User,
) -> None:
    """Вывести профиль пользователя: статусы и прогресс по играм."""
    played = [
        progress
        for progress in sessions_module.user_progress(sessions, games, user)
        if progress.hours
    ]
    statuses = stats_module.count_by_status(games, sessions, user)
    session_count = len(sessions_module.active_sessions(sessions, user=user))
    hours = sessions_module.hours_played(sessions, user=user)

    print_title(f"Профиль: {user.name}")
    print(f"Email:             {user.email}")
    print(f"Сессий записано:   {session_count}")
    print(f"Всего сыграно:     {hours:.1f} ч")
    print("Игры по статусам:")
    for status, count in statuses.items():
        print(f"  {status:<18}{count}")
    print("Прогресс по играм:")
    if not played:
        print("  пользователь ещё не играл")
    for progress in played:
        print(
            f"  {progress.game.title[:21]:<22}{progress}, "
            f"осталось {progress.hours_left:.1f} ч"
        )
    print("=" * LINE_WIDTH)


def show_sessions(sessions: list[GameSession]) -> None:
    """Вывести все игровые сессии, включая отменённые."""
    if not sessions:
        print("Игровые сессии ещё не записаны.")
        return
    for session in sorted(sessions, key=lambda item: item.date):
        print(session)


def show_stats(
    games: list[Game],
    users: list[User],
    sessions: list[GameSession],
) -> None:
    """Вывести сводную статистику библиотеки."""
    report = stats_module.library_stats(games, users, sessions)
    genres = ", ".join(report["genres"]) or "-"
    print_title("Статистика библиотеки")
    print(f"Игр в библиотеке:   {report['games']}")
    print(f"Пользователей:      {report['users']}")
    print(f"Записано сессий:    {report['sessions']}")
    print(f"Отменено сессий:    {report['cancelled']}")
    print(f"Всего сыграно:      {report['hours']:.1f} ч")
    print(f"Средняя оценка:     {report['average_rating']:.1f}")
    print(f"Жанры:              {genres}")
    print("Игры по платформам:")
    for platform, count in report["platforms"].items():
        print(f"  {platform:<18}{count}")
    if report["top"]:
        print("Больше всего сыграно:")
        for game, hours in report["top"]:
            print(f"  {game.title[:30]:<32}{hours:.1f} ч")
    if report["players"]:
        print("Самые активные игроки:")
        for user, hours in report["players"]:
            print(f"  {user.name[:30]:<32}{hours:.1f} ч")


def summary(obj: object) -> str:
    """Вернуть первую строку документации объекта."""
    doc = inspect.getdoc(obj)
    if not doc:
        return "нет описания"
    return doc.splitlines()[0]


def show_class_help(cls: type) -> None:
    """Вывести описание класса, его методов и свойств."""
    print(f"  class {cls.__name__} - {summary(cls)}")
    for name, member in vars(cls).items():
        if name.startswith("_") and name not in HELP_DUNDERS:
            continue
        if isinstance(member, property):
            print(f"    .{name} (свойство) - {summary(member)}")
            continue
        label = ""
        if isinstance(member, (staticmethod, classmethod)):
            label = f" @{type(member).__name__}"
            member = member.__func__
        if inspect.isfunction(member):
            print(f"    .{name}{inspect.signature(member)}{label}")
            print(f"        {summary(member)}")


def show_functions_help() -> None:
    """Вывести справку по классам и функциям проекта.

    Справка формируется средствами интроспекции: имена, сигнатуры и
    документирующие строки читаются из модулей во время выполнения.
    """
    for module in HELP_MODULES:
        print_title(f"Модуль {module.__name__.replace('.', '/')}.py")
        print(summary(module))
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__:
                show_class_help(cls)
        functions = inspect.getmembers(module, inspect.isfunction)
        for name, function in functions:
            if function.__module__ != module.__name__:
                continue
            print(f"  {name}{inspect.signature(function)}")
            print(f"    {summary(function)}")


def add_game_dialog(games: list[Game]) -> None:
    """Запросить данные новой игры и добавить её в библиотеку."""
    title = utils.input_text("Название игры: ")
    genre = utils.input_text("Жанр (Enter - пропустить): ", "Не указан")
    print("Платформа:")
    platform = utils.input_choice(
        "Выберите платформу: ", games_module.PLATFORMS
    )
    release_year = utils.input_int(
        "Год выпуска: ", min_value=games_module.FIRST_GAME_YEAR
    )
    hours_total = utils.input_float(
        "Примерное время прохождения, ч: ", min_value=0.1
    )
    rating = utils.input_int(
        "Ваша оценка от 1 до 10 (Enter - пропустить): ",
        min_value=0,
        max_value=games_module.MAX_RATING,
        default=0,
    )
    game = games_module.add_game(
        games, title, genre, platform, release_year, hours_total, rating
    )
    print(f"Игра добавлена: {game}, идентификатор {game.id}.")


def find_games_dialog(games: list[Game], sessions: list[GameSession]) -> None:
    """Найти игры по подстроке и вывести результат."""
    query = utils.input_text("Что ищем: ")
    found = games_module.find_games(games, query)
    if not found:
        print("Ничего не найдено.")
        return
    show_games(found, sessions)


def filter_games_dialog(
    games: list[Game],
    sessions: list[GameSession],
) -> None:
    """Отобрать игры выбранной платформы."""
    platform = utils.input_choice(
        "Выберите платформу: ", games_module.PLATFORMS
    )
    selected = games_module.filter_games_by_platform(games, platform)
    if not selected:
        print(f"Игр для платформы {platform} в библиотеке нет.")
        return
    show_games(selected, sessions)


def sort_games_dialog(games: list[Game], sessions: list[GameSession]) -> None:
    """Вывести игры в выбранном порядке сортировки."""
    labels = (
        "по названию",
        "по году выпуска",
        "по оценке",
        "по времени прохождения",
    )
    print("Порядок сортировки:")
    label = utils.input_choice("Выберите порядок: ", labels)
    sort_key = games_module.SORT_KEYS[labels.index(label)]
    show_games(games_module.sort_games(games, sort_key), sessions)


def game_card_dialog(
    games: list[Game],
    users: list[User],
    sessions: list[GameSession],
) -> None:
    """Найти игру по идентификатору и вывести её карточку."""
    game_id = utils.input_int("Идентификатор игры: ", min_value=1)
    game = games_module.get_game(games, game_id)
    show_game_card(users, sessions, game)


def remove_game_dialog(
    games: list[Game],
    sessions: list[GameSession],
) -> None:
    """Удалить игру вместе с её игровыми сессиями."""
    game_id = utils.input_int("Идентификатор игры: ", min_value=1)
    game = games_module.remove_game(games, game_id)
    removed = sessions_module.remove_game_sessions(sessions, game)
    print(f"Игра «{game.title}» удалена, сессий удалено: {removed}.")


def find_users_dialog(users: list[User], sessions: list[GameSession]) -> None:
    """Найти пользователей по подстроке имени или почты."""
    query = utils.input_text("Имя или адрес почты: ")
    found = users_module.find_users(users, query)
    if not found:
        print("Никто не найден.")
        return
    show_users(found, sessions)


def user_profile_dialog(
    games: list[Game],
    users: list[User],
    sessions: list[GameSession],
) -> None:
    """Найти пользователя по идентификатору и вывести его профиль."""
    user_id = utils.input_int("Идентификатор пользователя: ", min_value=1)
    user = users_module.get_user(users, user_id)
    show_user_profile(games, sessions, user)


def add_user_dialog(users: list[User]) -> None:
    """Запросить данные нового пользователя и добавить его."""
    name = utils.input_text("Имя пользователя: ")
    email = utils.input_text("Адрес электронной почты: ")
    user = users_module.add_user(users, name, email)
    print(f"Пользователь добавлен: {user}, идентификатор {user.id}.")


def create_new_session(
    games: list[Game],
    users: list[User],
    sessions: list[GameSession],
) -> None:
    """Записать игровую сессию пользователя по игре.

    Диалог находит объекты User и Game по идентификаторам, а саму
    сессию создаёт функция log_session(): она проверяет, свободен ли
    день, связывает сессию с пользователем и игрой и добавляет её в
    коллекцию.
    """
    if not users or not games:
        print("Для записи сессии нужны хотя бы один пользователь и игра.")
        return
    user_id = utils.input_int("Идентификатор пользователя: ", min_value=1)
    user = users_module.get_user(users, user_id)
    game_id = utils.input_int("Идентификатор игры: ", min_value=1)
    game = games_module.get_game(games, game_id)
    session_date = utils.input_date(
        "Дата сессии ДД.ММ.ГГГГ (Enter - сегодня): "
    )
    hours = utils.input_float("Сколько часов сыграно: ", min_value=0.1)
    session = sessions_module.log_session(
        sessions, user, game, session_date, hours
    )
    if session is None:
        day = session_date.strftime(sessions_module.DATE_FORMAT)
        print(
            f"У пользователя {user.name} уже есть сессия по игре "
            f"«{game.title}» за {day}."
        )
        return
    progress = sessions_module.get_progress(sessions, user, game)
    print(f"Записано. {session}")
    print(f"Прогресс {user.name}: {progress}")


def cancel_session_dialog(sessions: list[GameSession]) -> None:
    """Отменить игровую сессию: она остаётся в истории как отменённая."""
    session_id = utils.input_int("Идентификатор сессии: ", min_value=1)
    session = sessions_module.cancel_session(sessions, session_id)
    session_date = session.date.strftime(sessions_module.DATE_FORMAT)
    print(f"Сессия {session.id} за {session_date} отменена.")


def print_menu() -> None:
    """Вывести меню приложения, сгруппированное по разделам."""
    print_title("Система управления игровой библиотекой")
    number = 0
    for section, items in MENU_SECTIONS:
        print(f"{section}:")
        for item in items:
            number += 1
            print(f"{number:>4}. {item}")
    print("   0. Выход")


def load_data() -> tuple[list[Game], list[User], list[GameSession]]:
    """Загрузить коллекции объектов из JSON-файлов.

    При повреждённых файлах программа не
    завершается: выводится предупреждение и работа начинается с
    пустой библиотеки.
    """
    try:
        games, users, sessions = storage.load_library()
    except ValueError as error:
        print(f"Предупреждение: {error}")
        print("Работа продолжится с пустой библиотекой.")
        return [], [], []
    return games, users, sessions


def save_data(
    games: list[Game],
    users: list[User],
    sessions: list[GameSession],
) -> None:
    """Сохранить коллекции объектов в JSON-файлы."""
    try:
        storage.save_games(games)
        storage.save_users(users)
        storage.save_sessions(sessions)
    except ValueError as error:
        print(f"Ошибка сохранения: {error}")


def handle_choice(
    choice: int,
    games: list[Game],
    users: list[User],
    sessions: list[GameSession],
) -> bool:
    """Выполнить выбранный пункт меню.

    Возвращает True, если данные проекта изменились и их нужно
    сохранить в файлы.
    """
    actions: dict[int, Callable[[], None]] = {
        1: lambda: show_games(games, sessions),
        2: lambda: find_games_dialog(games, sessions),
        3: lambda: filter_games_dialog(games, sessions),
        4: lambda: sort_games_dialog(games, sessions),
        5: lambda: game_card_dialog(games, users, sessions),
        6: lambda: add_game_dialog(games),
        7: lambda: remove_game_dialog(games, sessions),
        8: lambda: show_users(users, sessions),
        9: lambda: find_users_dialog(users, sessions),
        10: lambda: user_profile_dialog(games, users, sessions),
        11: lambda: add_user_dialog(users),
        12: lambda: create_new_session(games, users, sessions),
        13: lambda: cancel_session_dialog(sessions),
        14: lambda: show_sessions(sessions),
        15: lambda: show_stats(games, users, sessions),
        16: show_functions_help,
    }
    actions[choice]()
    return choice in CHANGING_CHOICES


def describe_error(error: Exception) -> str:
    """Вернуть текст ошибки без служебных кавычек KeyError."""
    if error.args:
        return str(error.args[0])
    return str(error)


def main() -> None:
    """Точка запуска приложения: цикл меню и вызов функций проекта.

    Ошибки предметной области и прерывание ввода обрабатываются:
    программа завершается предсказуемо и сохраняет данные.
    """
    games, users, sessions = load_data()
    while True:
        print_menu()
        try:
            choice = utils.input_int(
                "Выберите действие: ",
                min_value=0,
                max_value=len(MENU_ITEMS),
            )
            if choice == 0:
                break
            changed = handle_choice(choice, games, users, sessions)
        except (ValueError, KeyError) as error:
            print(f"Ошибка: {describe_error(error)}")
            continue
        except (EOFError, KeyboardInterrupt):
            print("\nВвод прерван.")
            break
        if changed:
            save_data(games, users, sessions)
    save_data(games, users, sessions)
    print("Данные сохранены. До встречи!")


if __name__ == "__main__":
    main()
