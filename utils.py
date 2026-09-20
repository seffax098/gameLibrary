"""Вспомогательные функции безопасного ввода данных.

При некорректном вводе запрос повторяется: программа не завершается
аварийно, а сообщает пользователю о характере ошибки.
"""

from datetime import date, datetime

DATE_FORMATS: tuple[str, ...] = ("%d.%m.%Y", "%Y-%m-%d")


def input_text(prompt: str, default: str = "") -> str:
    """Запросить строку; пустой ввод заменяется значением default."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        if default:
            return default
        print("Ошибка: значение не может быть пустым.")


def input_int(
    prompt: str,
    min_value: int | None = None,
    max_value: int | None = None,
    default: int | None = None,
) -> int:
    """Запросить у пользователя целое число в заданных границах."""
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("Ошибка: введите целое число.")
            continue
        if min_value is not None and value < min_value:
            print(f"Ошибка: значение не меньше {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print(f"Ошибка: значение не больше {max_value}.")
            continue
        return value


def input_float(prompt: str, min_value: float = 0.0) -> float:
    """Запросить у пользователя дробное число не меньше min_value."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            print("Ошибка: введите число, например 12.5.")
            continue
        if value < min_value:
            print(f"Ошибка: значение не меньше {min_value}.")
            continue
        return value


def input_date(prompt: str) -> date:
    """Запросить дату в формате ДД.ММ.ГГГГ или ГГГГ-ММ-ДД.

    Пустой ввод означает сегодняшнюю дату.
    """
    while True:
        raw = input(prompt).strip()
        if not raw:
            return date.today()
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(raw, date_format).date()
            except ValueError:
                continue
        print("Ошибка: введите дату в формате ДД.ММ.ГГГГ.")


def input_choice(prompt: str, options: tuple[str, ...]) -> str:
    """Предложить выбрать один из вариантов по номеру."""
    for number, option in enumerate(options, start=1):
        print(f"  {number}. {option}")
    index = input_int(prompt, min_value=1, max_value=len(options))
    return options[index - 1]
