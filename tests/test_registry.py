from __future__ import annotations

import pytest
from django.test import override_settings
from django_q.models import Schedule
from model_bakery import baker

from django_q_registry.registry import TaskRegistry


@pytest.fixture
def registry():
    # clearing the registry before each test, since the registry
    # autodiscovers all tasks in project/apps. we could mock or
    # add a `pytest_is_running` check to the autodiscover_tasks
    # method, but this is clearer I think? -JT
    ret = TaskRegistry()
    ret.registered_tasks.clear()
    return ret


def test_decoration(registry):
    @registry.register(name="test_task")
    def test_task():
        return "test"

    assert len(registry.registered_tasks) == 1


def test_function_call(registry):
    def test_task():
        return "test"

    registry.register(test_task, name="test_task")

    assert len(registry.registered_tasks) == 1


@override_settings(
    Q_REGISTRY={
        "TASKS": [
            {
                "func": "tests.test_registry.test_settings",
                "name": "Task from settings",
            },
        ],
    }
)
def test_settings(registry):
    registry._register_settings()

    assert len(registry.registered_tasks) == 1


def test_function_is_callable(registry):
    @registry.register(name="test_task")
    def test_task():
        return "test"

    assert test_task() == "test"


def test_function_is_callable_with_args(registry):
    @registry.register(name="test_task")
    def test_task(arg):
        return arg

    assert test_task("test") == "test"


def test_function_name(registry):
    @registry.register(name="test_task")
    def test_task():
        return "test"

    assert test_task.__name__ == "test_task"


def test_register_no_name(registry):
    @registry.register()
    def test_task():
        return "test"

    tasks = list(registry.registered_tasks)

    assert len(tasks) == 1
    assert tasks[0].name == "test_task"


@pytest.mark.django_db
def test_register_all_legacy_suffix(registry):
    # add a task to the registry
    def test_task():
        return "test"

    registry.register(test_task, name="test_task")

    # simulate both the new and legacy scheduled tasks already being in the db
    baker.make(
        "django_q.Schedule",
        name="test_task - QREGISTRY",
        func="tests.test_registry.test_task",
    )
    baker.make(
        "django_q.Schedule",
        name="test_task - CRON",
        func="tests.test_registry.test_task",
    )

    assert Schedule.objects.count() == 2

    registry.register_all()

    assert Schedule.objects.count() == 1
    assert Schedule.objects.first().name == "test_task - QREGISTRY"
