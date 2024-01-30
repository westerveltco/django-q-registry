from __future__ import annotations

import logging
import multiprocessing

from django.conf import settings

pytest_plugins = []  # type: ignore


# Settings fixtures to bootstrap our tests
def pytest_configure(config):  # noqa: ARG001
    logging.disable(logging.CRITICAL)

    settings.configure(
        ALLOWED_HOSTS=["*"],
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            }
        },
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            },
        },
        Q_CLUSTER={
            "name": "ORM",
            "workers": multiprocessing.cpu_count() * 2 + 1,
            "timeout": 60,
            "retry": 120,
            "queue_limit": 50,
            "bulk": 10,
            "orm": "default",
        },
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        INSTALLED_APPS=[
            "django_q",
            "django_q_registry",
        ],
        LOGGING_CONFIG=None,
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        SECRET_KEY="NOTASECRET",
        USE_TZ=True,
    )
