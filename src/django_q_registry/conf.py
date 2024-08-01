from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from ._typing import override

DJANGO_Q_REGISTRY_SETTINGS_NAME = "Q_REGISTRY"


@dataclass(frozen=True)
class AppSettings:
    PERIODIC_TASK_SUFFIX: str = " - QREGISTRY"
    TASKS: list[dict[str, object]] = []

    @override
    def __getattribute__(self, __name: str) -> object:
        user_settings = getattr(settings, DJANGO_Q_REGISTRY_SETTINGS_NAME, {})
        return user_settings.get(__name, super().__getattribute__(__name))  # pyright: ignore[reportAny]


app_settings = AppSettings()
