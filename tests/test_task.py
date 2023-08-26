from __future__ import annotations

from django_q_registry.registry import Task


def test_task_equality():
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


def test_different_kwargs():
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
