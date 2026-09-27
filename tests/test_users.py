"""Тесты класса User и функций работы с коллекцией пользователей."""

import pytest

from models import User
from models.users import add_user, find_users, get_user


def test_user_creation() -> None:
    """Конструктор сохраняет данные в атрибутах объекта."""
    user = User(1, "Иван Петров", "ivan@example.com")
    assert user.id == 1
    assert user.name == "Иван Петров"
    assert user.email == "ivan@example.com"


def test_user_str() -> None:
    """Строковое представление содержит имя и адрес почты."""
    user = User(1, "Иван Петров", "ivan@example.com")
    assert str(user) == "Иван Петров <ivan@example.com>"


def test_user_email_is_normalized() -> None:
    """Пробелы вокруг данных убираются, почта - в нижнем регистре."""
    user = User(1, "  Анна  ", " Anna@Example.COM ")
    assert user.name == "Анна"
    assert user.email == "anna@example.com"


@pytest.mark.parametrize(
    "name, email",
    [
        ("", "ivan@example.com"),
        ("Иван", "ivan.example.com"),
        ("Иван", "ivan@example"),
        ("Иван", "iv an@example.com"),
    ],
)
def test_user_rejects_invalid_data(name: str, email: str) -> None:
    """Пустое имя или некорректная почта вызывают ValueError."""
    with pytest.raises(ValueError):
        User(1, name, email)


def test_validate_email() -> None:
    """Статический метод проверяет формат почты."""
    assert User.validate_email("ivan@example.com")
    assert not User.validate_email("ivan@")


def test_user_from_data() -> None:
    """from_data() создаёт объект User из данных JSON."""
    data = {"id": 7, "name": "Анна Смирнова", "email": "anna@example.com"}
    user = User.from_data(data)
    assert isinstance(user, User)
    assert user.id == 7
    assert user.to_data() == data


def test_add_user() -> None:
    """add_user() создаёт объект User и добавляет его в коллекцию."""
    users: list[User] = []
    user = add_user(users, "Иван Петров", "ivan@example.com")
    assert users == [user]
    assert add_user(users, "Анна", "anna@example.com").id == 2


def test_add_user_rejects_duplicate_email() -> None:
    """Повторный адрес почты вызывает ValueError."""
    users: list[User] = []
    add_user(users, "Иван Петров", "ivan@example.com")
    with pytest.raises(ValueError):
        add_user(users, "Другой Иван", "IVAN@example.com")
    assert len(users) == 1


def test_find_users() -> None:
    """Поиск работает по имени и по адресу почты."""
    users: list[User] = []
    add_user(users, "Иван Петров", "ivan@example.com")
    add_user(users, "Анна Смирнова", "anna@example.com")
    assert [user.name for user in find_users(users, "петров")] == [
        "Иван Петров"
    ]
    assert [user.id for user in find_users(users, "anna@")] == [2]
    assert not find_users(users, "олег")


def test_get_user() -> None:
    """Пользователь находится по идентификатору, иначе KeyError."""
    users: list[User] = []
    user = add_user(users, "Иван Петров", "ivan@example.com")
    assert get_user(users, 1) is user
    with pytest.raises(KeyError):
        get_user(users, 2)
