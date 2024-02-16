from __future__ import annotations

import pytest
from django.test import override_settings
from django_q.models import Schedule
from model_bakery import baker

from django_q_registry.models import Task
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


def test_function_is_not_callable_or_string(registry):
    with pytest.raises(TypeError):
        registry._register_task(func=5)


def test_function_string_is_not_formatted_correctly(registry):
    with pytest.raises(ImportError):
        registry._register_task(func="test_task")


def test_function_str_is_not_callable(registry):
    with pytest.raises(ImportError):
        registry._register_task(func="tests.test_task")


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
    schedule = baker.make(
        "django_q.Schedule",
        name="test_task - QREGISTRY",
        func="tests.test_registry.test_task",
    )
    registry.registered_tasks.add(
        baker.make("django_q_registry.Task", q_schedule=schedule)
    )

    baker.make(
        "django_q.Schedule",
        name="test_task - CRON",
        func="tests.test_registry.test_task",
    )

    assert Schedule.objects.count() == 2

    Task.objects.create_from_registry(registry)
    Task.objects.delete_dangling_objects(registry)

    assert Schedule.objects.count() == 1
    assert Schedule.objects.first().name == "test_task - QREGISTRY"


def test_issue_6_regression(registry):
    # https://github.com/westerveltco/django-q-registry/issues/6
    from django.core.mail import send_mail
    from django.utils import timezone

    base_kwargs = {
        "from_email": "from@example.com",
        "recipient_list": ["to@example.com"],
    }
    now = timezone.now()

    registry.register(
        send_mail,
        name="Send periodic test email",
        next_run=now,
        schedule_type=Schedule.MINUTES,
        minutes=5,
        kwargs={
            "subject": "Test email from reminders",
            "message": "This is a test email.",
            **base_kwargs,
        },
    )

    assert len(registry.registered_tasks) == 1

    task = list(registry.registered_tasks)[0]

    assert task == Task(
        name="Send periodic test email",
        func="django.core.mail.send_mail",
        kwargs={
            "next_run": now,
            "schedule_type": Schedule.MINUTES,
            "minutes": 5,
            "kwargs": {
                "subject": "Test email from reminders",
                "message": "This is a test email.",
                "from_email": "from@example.com",
                "recipient_list": ["to@example.com"],
            },
        },
    )
