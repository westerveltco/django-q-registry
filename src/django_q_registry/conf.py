from __future__ import annotations

from typing import Any
from typing import ClassVar

from django.conf import settings


class AppSettings:
    DEFAULT_SETTINGS: ClassVar[dict[str, Any]] = {
        "PERIODIC_TASK_SUFFIX": " - QREGISTRY",
        "TASKS": [],
    }

    def __getattr__(self, key):
        return self.get(key)

    def get(self, key):
        user_settings = getattr(settings, "Q_REGISTRY", {})
        return user_settings.get(key, self.DEFAULT_SETTINGS.get(key))


app_settings = AppSettings()
