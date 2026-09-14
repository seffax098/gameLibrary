import sys
from datetime import date

CURRENT_YEAR = date.today().year
FIRST_GAME_YEAR = 1958
LINE_WIDTH = 50


def print_header():
    print("=" * LINE_WIDTH)
    print("Система управления игровой библиотекой".center(LINE_WIDTH))
    print("=" * LINE_WIDTH)
    print("Добавление новой игры в библиотеку\n")


def read_title():
    title = input("Название игры: ").strip()
    if title == "":
        sys.exit("Ошибка: название игры не может быть пустым.")
    return title


def read_genre():
    genre = input("Жанр (Enter - пропустить): ").strip().capitalize()
    if genre == "":
        genre = "Не указан"
    return genre


def read_platform():
    platform_code = input("Платформа (1 - PC, 2 - PlayStation, 3 - Xbox, 4 - Nintendo Switch): ").strip()
    if platform_code == "1":
        return "PC"
    elif platform_code == "2":
        return "PlayStation"
    elif platform_code == "3":
        return "Xbox"
    elif platform_code == "4":
        return "Nintendo Switch"
    else:
        sys.exit("Ошибка: выберите платформу от 1 до 4.")


def read_release_year():
    year_input = input("Год выпуска: ").strip()
    if not year_input.isdigit():
        sys.exit("Ошибка: год выпуска должен быть целым числом.")
    release_year = int(year_input)
    if release_year < FIRST_GAME_YEAR or release_year > CURRENT_YEAR:
        sys.exit(f"Ошибка: год выпуска должен быть от {FIRST_GAME_YEAR} до {CURRENT_YEAR}.")
    return release_year


def read_non_negative_number(prompt, error_message):
    value_input = input(prompt).strip().replace(",", ".")
    if not value_input.replace(".", "", 1).isdigit():
        sys.exit(error_message)
    return float(value_input)


def read_hours_played():
    return read_non_negative_number(
        "Сыграно часов: ",
        "Ошибка: количество часов должно быть неотрицательным числом.",
    )


def read_hours_total():
    hours_total = read_non_negative_number(
        "Примерное время прохождения, ч: ",
        "Ошибка: время прохождения должно быть неотрицательным числом.",
    )
    if hours_total == 0:
        sys.exit("Ошибка: время прохождения должно быть больше нуля.")
    return hours_total


def read_rating():
    rating_input = input("Ваша оценка от 1 до 10 (Enter - пропустить): ").strip()
    if rating_input == "":
        return 0
    if not rating_input.isdigit():
        sys.exit("Ошибка: оценка должна быть целым числом.")
    rating = int(rating_input)
    if rating < 1 or rating > 10:
        sys.exit("Ошибка: оценка должна быть от 1 до 10.")
    return rating


def get_era(game_age):
    if game_age <= 1:
        return "новинка"
    elif game_age >= 15:
        return "классика"
    else:
        return "современная игра"


def calculate_progress(hours_played, hours_total):
    return min(hours_played / hours_total * 100, 100)


def get_status(hours_played, progress):
    if hours_played == 0:
        return "Не начата"
    elif progress >= 100:
        return "Пройдена"
    else:
        return "В процессе"


def make_progress_bar(progress):
    filled = int(progress // 10)
    return "#" * filled + "-" * (10 - filled)


def get_rating_label(rating):
    has_rating = bool(rating)
    if not has_rating:
        return "не выставлена"
    elif rating >= 9:
        return f"{rating}/10 - шедевр"
    elif rating >= 7:
        return f"{rating}/10 - хорошая игра"
    elif rating >= 5:
        return f"{rating}/10 - средняя игра"
    else:
        return f"{rating}/10 - разочарование"


def print_game_card(title, genre, platform, release_year, hours_played, hours_total, rating):
    game_age = CURRENT_YEAR - release_year
    era = get_era(game_age)
    progress = calculate_progress(hours_played, hours_total)
    status = get_status(hours_played, progress)
    progress_bar = make_progress_bar(progress)
    hours_left = max(hours_total - hours_played, 0)
    rating_label = get_rating_label(rating)

    print()
    print("=" * LINE_WIDTH)
    print(f"Карточка игры: {title}")
    print("-" * LINE_WIDTH)
    print(f"Жанр:            {genre}")
    print(f"Платформа:       {platform}")
    print(f"Год выпуска:     {release_year} ({era}, лет с выхода: {game_age})")
    print(f"Прогресс:        [{progress_bar}] {progress:.0f}%")
    print(f"Статус:          {status}")
    print(f"Сыграно:         {hours_played:.1f} из {hours_total:.1f} ч")
    print(f"Осталось:        {hours_left:.1f} ч")
    print(f"Оценка:          {rating_label}")
    print("=" * LINE_WIDTH)


def main():
    print_header()
    title = read_title()
    genre = read_genre()
    platform = read_platform()
    release_year = read_release_year()
    hours_played = read_hours_played()
    hours_total = read_hours_total()
    rating = read_rating()
    print_game_card(title, genre, platform, release_year, hours_played, hours_total, rating)


if __name__ == "__main__":
    main()
