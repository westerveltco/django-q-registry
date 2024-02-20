from __future__ import annotations

import itertools

import pytest
from django_q.models import Schedule
from model_bakery import baker

from django_q_registry.conf import app_settings
from django_q_registry.management.commands import setup_periodic_tasks
from django_q_registry.models import Task
from django_q_registry.registry import registry

pytestmark = pytest.mark.django_db


@registry.register(name="test_task")
def task():
    return "test"


def test_setup_periodic_tasks():
    assert len(registry.registered_tasks) == 1
    assert Task.objects.count() == 0
    assert Schedule.objects.count() == 0

    setup_periodic_tasks.Command().handle()

    assert len(registry.registered_tasks) == 1
    assert len(registry.created_tasks) == 1
    assert Task.objects.count() == 1
    assert Schedule.objects.count() == 1


def test_setup_periodic_tasks_dangling_tasks():
    baker.make("django_q_registry.Task", _quantity=3)

    assert len(registry.registered_tasks) == 1
    assert Task.objects.count() == 3

    setup_periodic_tasks.Command().handle()

    assert len(registry.registered_tasks) == 1
    assert len(registry.created_tasks) == 1
    assert Task.objects.count() == 1


def test_setup_periodic_tasks_dangling_schedules():
    baker.make(
        "django_q.Schedule",
        name=itertools.cycle(
            [
                f"dangling_schedule{i}{app_settings.PERIODIC_TASK_SUFFIX}"
                for i in range(3)
            ]
        ),
        _quantity=3,
    )

    assert len(registry.registered_tasks) == 1
    assert Schedule.objects.count() == 3

    setup_periodic_tasks.Command().handle()

    assert len(registry.registered_tasks) == 1
    assert len(registry.created_tasks) == 1
    assert Schedule.objects.count() == 1


def test_setup_periodic_tasks_dangling_legacy_schedules():
    schedules = baker.make("django_q.Schedule", _quantity=3)
    baker.make(
        "django_q.Schedule",
        name=itertools.cycle([f"dangling_schedule{i} - CRON" for i in range(3)]),
        _quantity=len(schedules),
    )

    assert len(registry.registered_tasks) == 1
    assert Schedule.objects.count() == 6

    setup_periodic_tasks.Command().handle()

    assert len(registry.registered_tasks) == 1
    assert len(registry.created_tasks) == 1
    assert Schedule.objects.count() == 1 + len(schedules)
