from __future__ import annotations

import pytest
from model_bakery import baker

from django_q_registry.models import Task

pytestmark = pytest.mark.django_db


class TestTask:
    def test_task_equality_in_memory(self):
        task1 = Task(
            name="test",
            func="tests.test_task.test_task_equality",
            kwargs={"foo": "bar"},
        )
        task2 = Task(
            name="test",
            func="tests.test_task.test_task_equality",
            kwargs={"foo": "bar"},
        )

        assert task1 == task2

    def test_different_kwargs_in_memory(self):
        task1 = Task(
            name="test",
            func="tests.test_task.test_different_kwargs",
            kwargs={"foo": "bar"},
        )
        task2 = Task(
            name="test",
            func="tests.test_task.test_different_kwargs",
            kwargs={"baz": "qux"},
        )

        assert task1 != task2

    def test_same_kwargs_in_db(self):
        task1 = baker.make(
            "django_q_registry.Task",
            name="test",
            func="tests.test_task.test_task_equality",
            kwargs={"foo": "bar"},
        )
        task2 = baker.make(
            "django_q_registry.Task",
            name="test",
            func="tests.test_task.test_task_equality",
            kwargs={"foo": "bar"},
        )

        assert task1 != task2
