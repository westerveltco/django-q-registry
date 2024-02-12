from __future__ import annotations

from django.conf import settings
from django.test import override_settings

from django_q_registry.conf import app_settings


def test_default_settings():
    """Should be empty by default."""
    q_registry_settings = getattr(settings, "Q_REGISTRY", {})
    assert q_registry_settings == {}


def test_default_app_settings():
    assert app_settings.PERIODIC_TASK_SUFFIX == " - QREGISTRY"
    assert app_settings.TASKS == []


@override_settings(
    Q_REGISTRY={
        "PERIODIC_TASK_SUFFIX": " - TEST",
    }
)
def test_user_set_suffix():
    assert app_settings.PERIODIC_TASK_SUFFIX == " - TEST"


@override_settings(
    Q_REGISTRY={
        "TASKS": [
            {
                "name": "test",
                "func": "tests.test_conf.test_user_set_tasks",
            },
            {
                "name": "test2",
                "func": "tests.test_conf.test_user_set_tasks",
            },
        ],
    },
)
def test_user_set_tasks():
    assert len(app_settings.TASKS) == 2
