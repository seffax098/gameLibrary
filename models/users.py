"""Пользователи системы и функции работы с коллекцией пользователей.

Пользователь - игрок, который записывает игровые сессии по играм общей
библиотеки. Пользователи хранятся в списке объектов ``User``.
"""

import re

EMAIL_PATTERN: re.Pattern[str] = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class User:
    """Пользователь системы - игрок, ведущий учёт игровых сессий."""

    def __init__(self, user_id: int, name: str, email: str) -> None:
        """Создать пользователя, проверив имя и адрес электронной почты.

        Адрес приводится к нижнему регистру. При некорректных данных
        возбуждается исключение ValueError.
        """
        name = name.strip()
        email = email.strip().lower()
        if not name:
            raise ValueError("Имя пользователя не может быть пустым.")
        if not User.validate_email(email):
            raise ValueError(f"Некорректный адрес электронной почты: {email}")
        self.id = user_id
        self.name = name
        self.email = email

    def __str__(self) -> str:
        """Вернуть строковое представление пользователя."""
        return f"{self.name} <{self.email}>"

    @staticmethod
    def validate_email(email: str) -> bool:
        """Проверить формат адреса электронной почты."""
        return EMAIL_PATTERN.fullmatch(email.strip()) is not None

    @classmethod
    def from_data(cls, data: dict) -> "User":
        """Создать пользователя из набора данных, прочитанного из JSON."""
        return cls(int(data["id"]), data["name"], data["email"])

    def to_data(self) -> dict:
        """Вернуть данные пользователя для сохранения в JSON."""
        return {"id": self.id, "name": self.name, "email": self.email}

    def matches(self, query: str) -> bool:
        """Проверить, содержат ли имя или адрес почты подстроку."""
        query = query.strip().lower()
        return query in f"{self.name} {self.email}".lower()


def next_user_id(users: list[User]) -> int:
    """Вернуть свободный идентификатор для нового пользователя."""
    if not users:
        return 1
    return max(user.id for user in users) + 1


def add_user(users: list[User], name: str, email: str) -> User:
    """Создать пользователя, добавить его в коллекцию и вернуть его.

    Адрес электронной почты должен быть уникальным: при повторе
    возбуждается исключение ValueError.
    """
    user = User(next_user_id(users), name, email)
    if any(existing.email == user.email for existing in users):
        raise ValueError(f"Пользователь с адресом {user.email} уже есть.")
    users.append(user)
    return user


def find_user_by_id(users: list[User], user_id: int) -> User | None:
    """Найти пользователя по идентификатору.

    Если пользователя нет, возвращается None.
    """
    for user in users:
        if user.id == user_id:
            return user
    return None


def get_user(users: list[User], user_id: int) -> User:
    """Вернуть пользователя по идентификатору.

    Если пользователь не найден, возбуждается исключение KeyError.
    """
    user = find_user_by_id(users, user_id)
    if user is None:
        raise KeyError(f"Пользователь с идентификатором {user_id} не найден.")
    return user


def find_users(users: list[User], query: str) -> list[User]:
    """Найти пользователей по подстроке имени или адреса почты."""
    return [user for user in users if user.matches(query)]
