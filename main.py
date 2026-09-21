"""Консольное приложение «Система управления игровой библиотекой».

Модуль содержит функции вывода данных, обработчики пунктов меню и
точку запуска программы. Логика предметной области вынесена в модули
games, sessions, stats, storage и utils.
"""

import inspect

import games as games_module
import sessions as sessions_module
import stats as stats_module
import storage
import utils

LINE_WIDTH: int = 60
MENU_ITEMS: tuple[str, ...] = (
    "Показать библиотеку",
    "Найти игру по названию или жанру",
    "Отобрать игры по платформе",
    "Отсортировать игры",
    "Показать карточку игры",
    "Добавить игру",
    "Удалить игру",
    "Записать игровую сессию",
    "Отменить игровую сессию",
    "Показать игровые сессии",
    "Показать статистику библиотеки",
    "Справка по функциям проекта",
)


def print_title(text: str) -> None:
    """Вывести заголовок раздела."""
    print()
    print("=" * LINE_WIDTH)
    print(text.center(LINE_WIDTH))
    print("=" * LINE_WIDTH)


def show_games(games: dict[int, dict], sessions: list[dict]) -> None:
    """Вывести список игр в виде таблицы."""
    if not games:
        print("Библиотека пуста: добавьте первую игру.")
        return
    print(
        f"{'ID':<4}{'Название':<28}{'Платформа':<16}"
        f"{'Год':<6}{'Статус':<12}"
    )
    print("-" * LINE_WIDTH)
    for game_id, game in games.items():
        progress = sessions_module.get_game_progress(
            sessions, game_id, game["hours_total"]
        )
        print(
            f"{game_id:<4}{game['title'][:27]:<28}"
            f"{game['platform']:<16}{game['release_year']:<6}"
            f"{progress['status']:<12}"
        )


def show_game_card(
    games: dict[int, dict],
    sessions: list[dict],
    game_id: int,
) -> None:
    """Вывести подробную карточку игры.

    Карточка развивает вывод первоначального сценария ПР1: данные
    берутся из коллекций, а время игры - из записанных сессий.
    """
    game = games_module.get_game(games, game_id)
    era = games_module.get_era(game["release_year"])
    age = games_module.get_game_age(game["release_year"])
    progress = sessions_module.get_game_progress(
        sessions, game_id, game["hours_total"]
    )
    rating_label = games_module.get_rating_label(game["rating"])
    played = len(sessions_module.game_sessions(sessions, game_id))

    print_title(f"Карточка игры: {game['title']}")
    print(f"Жанр:            {game['genre']}")
    print(f"Платформа:       {game['platform']}")
    print(
        f"Год выпуска:     {game['release_year']} "
        f"({era}, лет с выхода: {age})"
    )
    print(
        f"Прогресс:        [{progress['bar']}] "
        f"{progress['progress']:.0f}%"
    )
    print(f"Статус:          {progress['status']}")
    print(
        f"Сыграно:         {progress['hours']:.1f} из "
        f"{game['hours_total']:.1f} ч"
    )
    print(f"Осталось:        {progress['hours_left']:.1f} ч")
    print(f"Сессий записано: {played}")
    print(f"Оценка:          {rating_label}")
    print("=" * LINE_WIDTH)


def show_sessions(sessions: list[dict], games: dict[int, dict]) -> None:
    """Вывести список игровых сессий."""
    if not sessions:
        print("Игровые сессии ещё не записаны.")
        return
    print(f"{'ID':<4}{'Игра':<28}{'Дата':<14}{'Часы':<6}")
    print("-" * LINE_WIDTH)
    for session in sorted(sessions, key=lambda item: item["date"]):
        game = games.get(session["game_id"], {})
        title = game.get("title", "игра удалена")
        session_date = session["date"].strftime("%d.%m.%Y")
        print(
            f"{session['id']:<4}{title[:27]:<28}"
            f"{session_date:<14}{session['hours']:<6.1f}"
        )


def show_stats(games: dict[int, dict], sessions: list[dict]) -> None:
    """Вывести сводную статистику библиотеки."""
    report = stats_module.library_stats(games, sessions)
    genres = ", ".join(report["genres"]) or "-"
    print_title("Статистика библиотеки")
    print(f"Игр в библиотеке:   {report['games']}")
    print(f"Записано сессий:    {report['sessions']}")
    print(f"Всего сыграно:      {report['hours']:.1f} ч")
    print(f"Средняя оценка:     {report['average_rating']:.1f}")
    print(f"Жанры:              {genres}")
    print("Игры по платформам:")
    for platform, count in report["platforms"].items():
        print(f"  {platform:<18}{count}")
    print("Игры по статусам:")
    for status, count in report["statuses"].items():
        print(f"  {status:<18}{count}")
    if report["top"]:
        print("Больше всего сыграно:")
        for title, hours in report["top"]:
            print(f"  {title[:30]:<32}{hours:.1f} ч")


def show_functions_help() -> None:
    """Вывести справку по функциям проекта.

    Справка формируется средствами интроспекции: имена, сигнатуры и
    документирующие строки читаются из модулей во время выполнения.
    """
    modules = (
        games_module,
        sessions_module,
        stats_module,
        storage,
        utils,
    )
    for module in modules:
        print_title(f"Модуль {module.__name__}.py")
        module_doc = inspect.getdoc(module) or "нет описания"
        print(module_doc.splitlines()[0])
        functions = inspect.getmembers(module, inspect.isfunction)
        for name, function in functions:
            if function.__module__ != module.__name__:
                continue
            summary = inspect.getdoc(function) or "нет описания"
            print(f"  {name}{inspect.signature(function)}")
            print(f"    {summary.splitlines()[0]}")


def add_game_dialog(games: dict[int, dict]) -> None:
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
    game_id = games_module.add_game(
        games, title, genre, platform, release_year, hours_total, rating
    )
    print(f"Игра добавлена, идентификатор: {game_id}.")


def find_games_dialog(games: dict[int, dict], sessions: list[dict]) -> None:
    """Найти игры по подстроке и вывести результат."""
    query = utils.input_text("Что ищем: ")
    found = games_module.find_games(games, query)
    if not found:
        print("Ничего не найдено.")
        return
    show_games(found, sessions)


def filter_games_dialog(
    games: dict[int, dict],
    sessions: list[dict],
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


def sort_games_dialog(games: dict[int, dict], sessions: list[dict]) -> None:
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
    ordered = dict(games_module.sort_games(games, sort_key))
    show_games(ordered, sessions)


def log_session_dialog(
    games: dict[int, dict],
    sessions: list[dict],
) -> None:
    """Записать игровую сессию для выбранной игры."""
    game_id = utils.input_int("Идентификатор игры: ", min_value=1)
    game = games_module.get_game(games, game_id)
    session_date = utils.input_date(
        "Дата сессии ДД.ММ.ГГГГ (Enter - сегодня): "
    )
    hours = utils.input_float("Сколько часов сыграно: ", min_value=0.1)
    session = sessions_module.log_session(
        sessions, game_id, session_date, hours
    )
    progress = sessions_module.get_game_progress(
        sessions, game_id, game["hours_total"]
    )
    print(
        f"Сессия {session['id']} записана. "
        f"Статус игры: {progress['status']} "
        f"({progress['progress']:.0f}%)."
    )


def cancel_session_dialog(sessions: list[dict]) -> None:
    """Отменить ранее записанную игровую сессию."""
    session_id = utils.input_int("Идентификатор сессии: ", min_value=1)
    session = sessions_module.cancel_session(sessions, session_id)
    session_date = session["date"].strftime("%d.%m.%Y")
    print(f"Сессия {session['id']} за {session_date} отменена.")


def remove_game_dialog(
    games: dict[int, dict],
    sessions: list[dict],
) -> None:
    """Удалить игру вместе с её игровыми сессиями."""
    game_id = utils.input_int("Идентификатор игры: ", min_value=1)
    game = games_module.remove_game(games, game_id)
    removed = sessions_module.cancel_game_sessions(sessions, game_id)
    print(f"Игра «{game['title']}» удалена, сессий удалено: {removed}.")


def print_menu() -> None:
    """Вывести меню приложения."""
    print_title("Система управления игровой библиотекой")
    for number, item in enumerate(MENU_ITEMS, start=1):
        print(f"{number:>2}. {item}")
    print(" 0. Выход")


def load_data() -> tuple[dict[int, dict], list[dict]]:
    """Загрузить данные проекта из JSON-файлов.

    При повреждённых файлах программа не завершается: выводится
    предупреждение и работа начинается с пустой библиотеки.
    """
    try:
        return storage.load_games(), storage.load_sessions()
    except ValueError as error:
        print(f"Предупреждение: {error}")
        print("Работа продолжится с пустой библиотекой.")
        return {}, []


def save_data(games: dict[int, dict], sessions: list[dict]) -> None:
    """Сохранить данные проекта в JSON-файлы."""
    try:
        storage.save_games(games)
        storage.save_sessions(sessions)
    except ValueError as error:
        print(f"Ошибка сохранения: {error}")


def handle_choice(
    choice: int,
    games: dict[int, dict],
    sessions: list[dict],
) -> bool:
    """Выполнить выбранный пункт меню.

    Возвращает True, если данные проекта изменились и их нужно
    сохранить в файлы.
    """
    if choice == 1:
        show_games(games, sessions)
    elif choice == 2:
        find_games_dialog(games, sessions)
    elif choice == 3:
        filter_games_dialog(games, sessions)
    elif choice == 4:
        sort_games_dialog(games, sessions)
    elif choice == 5:
        game_id = utils.input_int("Идентификатор игры: ", min_value=1)
        show_game_card(games, sessions, game_id)
    elif choice == 6:
        add_game_dialog(games)
        return True
    elif choice == 7:
        remove_game_dialog(games, sessions)
        return True
    elif choice == 8:
        log_session_dialog(games, sessions)
        return True
    elif choice == 9:
        cancel_session_dialog(sessions)
        return True
    elif choice == 10:
        show_sessions(sessions, games)
    elif choice == 11:
        show_stats(games, sessions)
    elif choice == 12:
        show_functions_help()
    return False


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
    games, sessions = load_data()
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
            changed = handle_choice(choice, games, sessions)
        except (ValueError, KeyError) as error:
            print(f"Ошибка: {describe_error(error)}")
            continue
        except (EOFError, KeyboardInterrupt):
            print("\nВвод прерван.")
            break
        if changed:
            save_data(games, sessions)
    save_data(games, sessions)
    print("Данные сохранены. До встречи!")


if __name__ == "__main__":
    main()
