# pyright: reportAny=false
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from django.conf import settings

from ._typing import override

DJANGO_Q_REGISTRY_SETTINGS_NAME = "Q_REGISTRY"


@dataclass(frozen=True)
class AppSettings:
    PERIODIC_TASK_SUFFIX: str = " - QREGISTRY"
    TASKS: list[dict[str, Any]] = field(default_factory=list)

    @override
    def __getattribute__(self, __name: str) -> object:
        user_settings = getattr(settings, DJANGO_Q_REGISTRY_SETTINGS_NAME, {})
        return user_settings.get(__name, super().__getattribute__(__name))


app_settings = AppSettings()
