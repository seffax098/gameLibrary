#!/usr/bin/env python
"""Утилита командной строки для управления Django-проектом.

Примеры: python manage.py runserver, python manage.py migrate,
python manage.py test.
"""
import os
import sys


def main() -> None:
    """Выполнить команду управления, переданную в аргументах."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gamelibrary.settings")
    try:
        # Импорт внутри функции: так выводится понятное сообщение,
        # если Django не установлен.
        # pylint: disable-next=import-outside-toplevel
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Проверьте, что он установлен "
            "и доступен через переменную окружения PYTHONPATH. Возможно, "
            "не активировано виртуальное окружение."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
