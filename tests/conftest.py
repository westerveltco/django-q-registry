from __future__ import annotations

import logging
import multiprocessing

from django.conf import settings

from .settings import DEFAULT_SETTINGS

pytest_plugins = []  # type: ignore


def pytest_configure(config):
    logging.disable(logging.CRITICAL)

    settings.configure(**DEFAULT_SETTINGS, **TEST_SETTINGS)


TEST_SETTINGS = {
    "INSTALLED_APPS": [
        "django.contrib.contenttypes",
        "django_q",
        "django_q_registry",
    ],
    "Q_CLUSTER": {
        "name": "ORM",
        "workers": multiprocessing.cpu_count() * 2 + 1,
        "timeout": 60,
        "retry": 120,
        "queue_limit": 50,
        "bulk": 10,
        "orm": "default",
    },
}
