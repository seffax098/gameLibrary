import sys
from datetime import date

CURRENT_YEAR = date.today().year
FIRST_GAME_YEAR = 1958
LINE_WIDTH = 50

print("=" * LINE_WIDTH)
print("Система управления игровой библиотекой".center(LINE_WIDTH))
print("=" * LINE_WIDTH)
print("Добавление новой игры в библиотеку\n")

title = input("Название игры: ").strip()
if title == "":
    sys.exit("Ошибка: название игры не может быть пустым.")

genre = input("Жанр (Enter - пропустить): ").strip().capitalize()
if genre == "":
    genre = "Не указан"

platform_code = input("Платформа (1 - PC, 2 - PlayStation, 3 - Xbox, 4 - Nintendo Switch): ").strip()
if platform_code == "1":
    platform = "PC"
elif platform_code == "2":
    platform = "PlayStation"
elif platform_code == "3":
    platform = "Xbox"
elif platform_code == "4":
    platform = "Nintendo Switch"
else:
    sys.exit("Ошибка: выберите платформу от 1 до 4.")


year_input = input("Год выпуска: ").strip()
if not year_input.isdigit():
    sys.exit("Ошибка: год выпуска должен быть целым числом.")
release_year = int(year_input)
if release_year < FIRST_GAME_YEAR or release_year > CURRENT_YEAR:
    sys.exit(f"Ошибка: год выпуска должен быть от {FIRST_GAME_YEAR} до {CURRENT_YEAR}.")

played_input = input("Сыграно часов: ").strip().replace(",", ".")
if not played_input.replace(".", "", 1).isdigit():
    sys.exit("Ошибка: количество часов должно быть неотрицательным числом.")
hours_played = float(played_input)

total_input = input("Примерное время прохождения, ч: ").strip().replace(",", ".")
if not total_input.replace(".", "", 1).isdigit():
    sys.exit("Ошибка: время прохождения должно быть неотрицательным числом.")
hours_total = float(total_input)
if hours_total == 0:
    sys.exit("Ошибка: время прохождения должно быть больше нуля.")

rating_input = input("Ваша оценка от 1 до 10 (Enter - пропустить): ").strip()
has_rating = bool(rating_input)
rating = 0
if has_rating:
    if not rating_input.isdigit():
        sys.exit("Ошибка: оценка должна быть целым числом.")
    rating = int(rating_input)
    if rating < 1 or rating > 10:
        sys.exit("Ошибка: оценка должна быть от 1 до 10.")

game_age = CURRENT_YEAR - release_year
if game_age <= 1:
    era = "новинка"
elif game_age >= 15:
    era = "классика"
else:
    era = "современная игра"

progress = min(hours_played / hours_total * 100, 100)
is_completed = progress >= 100
if hours_played == 0:
    status = "Не начата"
elif is_completed:
    status = "Пройдена"
else:
    status = "В процессе"

filled = int(progress // 10)
progress_bar = "#" * filled + "-" * (10 - filled)

hours_left = max(hours_total - hours_played, 0)

if not has_rating:
    rating_label = "не выставлена"
elif rating >= 9:
    rating_label = f"{rating}/10 - шедевр"
elif rating >= 7:
    rating_label = f"{rating}/10 - хорошая игра"
elif rating >= 5:
    rating_label = f"{rating}/10 - средняя игра"
else:
    rating_label = f"{rating}/10 - разочарование"


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
