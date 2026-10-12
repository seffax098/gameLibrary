"""Настройки Django-проекта gamelibrary.

Файл создан командой django-admin startproject (Django 5.2) и
дополнен настройками проекта: приложения, локализация, каталог данных.

Описание настроек:
https://docs.djangoproject.com/en/5.2/topics/settings/
Полный список настроек и их значений:
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

# Пути внутри проекта строятся от корня: BASE_DIR / 'подкаталог'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Настройки для разработки, не подходят для рабочего сервера.
# Чек-лист развёртывания:
# https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# ВНИМАНИЕ: на рабочем сервере секретный ключ должен храниться в тайне!
SECRET_KEY = (
    'django-insecure-'
    '^c6aci-%jrf6yaxx9m^au$-t!z6p$u+&tvbh(5!ku50nwoal3n'
)

# ВНИМАНИЕ: не включайте режим отладки на рабочем сервере!
DEBUG = True

ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]


# Подключённые приложения: встроенные приложения Django и
# приложения проекта (homepage, games, gamesessions).

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'homepage',
    'games',
    'gamesessions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gamelibrary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gamelibrary.wsgi.application'


# База данных. Пока в ней только служебные таблицы Django: данные
# библиотеки хранятся в JSON-файлах (см. DATA_DIR).
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Проверка надёжности паролей пользователей.
# https://docs.djangoproject.com/en/5.2/ref/settings/
#     #auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# Язык и часовой пояс.
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Статические файлы (CSS, JavaScript, изображения).
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Тип первичного ключа Django-моделей по умолчанию.
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Данные игровой библиотеки (JSON-хранилище ПР3).
# Путь строится от BASE_DIR, поэтому страницы находят файлы
# независимо от каталога, из которого запущен сервер.

DATA_DIR = BASE_DIR / 'data'
