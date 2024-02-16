from __future__ import annotations

import itertools

import pytest
from django_q.models import Schedule
from model_bakery import baker

from django_q_registry.conf import app_settings
from django_q_registry.models import Task
from django_q_registry.registry import TaskRegistry

pytestmark = pytest.mark.django_db


class TestTaskQuerySet:
    def test_create_in_memory(self):
        def test_task():
            pass

        task_kwargs = {
            "name": "test",
            "foo": "bar",
        }

        in_memory_task = Task.objects.create_in_memory(test_task, task_kwargs)

        assert not in_memory_task.pk
        assert in_memory_task.name == "test"
        assert in_memory_task.func == "tests.test_models.test_task"

        task_instance = Task(
            name="test",
            func="tests.test_models.test_task",
            kwargs={"foo": "bar"},
        )

        assert task_instance == in_memory_task

    def test_create_in_memory_no_name(self):
        def test_task():
            pass

        test_kwargs = {
            "foo": "bar",
        }

        in_memory_task = Task.objects.create_in_memory(test_task, test_kwargs)

        assert in_memory_task.name == "test_task"

    def test_create_from_registry(self):
        def test_task():
            pass

        def test_foo():
            pass

        def test_baz():
            pass

        tasks = []

        # duplicate tasks
        # +1
        tasks.extend(
            [
                baker.prepare(
                    "django_q_registry.Task",
                    name="test_task",
                    func="tests.test_models.test_task",
                    kwargs={"kwargs": {"foo": "bar"}},
                )
                for _ in range(2)
            ]
        )
        # completely unique tasks
        # +2
        tasks.append(
            baker.prepare(
                "django_q_registry.Task",
                name="test_foo",
                func="tests.test_models.test_foo",
                kwargs={"kwargs": {"foo": "bar"}},
            )
        )
        tasks.append(
            baker.prepare(
                "django_q_registry.Task",
                name="test_baz",
                func="tests.test_models.test_baz",
                kwargs={"kwargs": {"baz": "qux"}},
            )
        )
        # similar tasks with different names but same function and kwargs
        # +2
        tasks.extend(
            [
                baker.prepare("django_q_registry.Task", name=f"different_names_{_}")
                for _ in range(2)
            ]
        )
        # similar tasks with different functions but same names and kwargs
        # +2
        tasks.extend(
            [
                baker.prepare(
                    "django_q_registry.Task",
                    func=f"tests.test_models.{test_func.__name__}",
                )
                for test_func in [test_foo, test_baz]
            ]
        )
        # similar tasks with different kwargs but same names and functions
        # +2
        tasks.extend(
            [
                baker.prepare("django_q_registry.Task", kwargs={"kwargs": {k: v}})
                for k, v in {"foo": "bar", "baz": "qux"}.items()
            ]
        )

        registry = TaskRegistry(registered_tasks=set(tasks))

        registered_tasks = Task.objects.create_from_registry(registry)

        assert len(registered_tasks) == 9

    def test_register_existing_task(self, caplog):
        existing_task = baker.make("django_q_registry.Task")
        registry = TaskRegistry(registered_tasks=set([existing_task]))

        with caplog.at_level("ERROR"):
            Task.objects.create_from_registry(registry)

        assert f"Task {existing_task.pk} has already been registered" in caplog.text

    def test_register_existing_task_with_new_task(self, caplog):
        new_task = baker.prepare("django_q_registry.Task", name="new_task")
        existing_task = baker.make("django_q_registry.Task", name="existing_task")
        registry = TaskRegistry(registered_tasks=set([new_task, existing_task]))

        with caplog.at_level("ERROR"):
            Task.objects.create_from_registry(registry)

        assert Task.objects.count() == 2
        assert Task.objects.filter(name=new_task.name).exists()
        assert f"Task {existing_task.pk} has already been registered" in caplog.text

    def test_register_schedule_creation(self):
        tasks = baker.prepare("django_q_registry.Task", _quantity=3)

        assert Schedule.objects.count() == 0

        registry = TaskRegistry(registered_tasks=set(tasks))

        registered_tasks = Task.objects.create_from_registry(registry)

        assert (
            Schedule.objects.filter(
                registered_task__in=[task.pk for task in registered_tasks]
            ).count()
            == 3
        )

    def test_register_schedule_update(self):
        schedule = baker.make("django_q.Schedule")
        task = baker.prepare("django_q_registry.Task", q_schedule=schedule)
        registry = TaskRegistry(registered_tasks=set([task]))

        registered_tasks = Task.objects.create_from_registry(registry)

        assert (
            Schedule.objects.filter(
                registered_task__in=[task.pk for task in registered_tasks]
            ).count()
            == 1
        )

    def test_exclude_registered(self):
        registry = TaskRegistry(
            registered_tasks=set(baker.make("django_q_registry.Task", _quantity=3))
        )

        excluded_tasks = Task.objects.exclude_registered(registry)

        assert excluded_tasks.count() == 0

    def test_exclude_registered_with_unregistered_tasks(self):
        registry = TaskRegistry(
            registered_tasks=set(baker.make("django_q_registry.Task", _quantity=3))
        )
        unregistered_tasks = baker.make("django_q_registry.Task", _quantity=3)

        excluded_tasks = Task.objects.exclude_registered(registry)

        assert excluded_tasks.count() == 3
        assert all(task in unregistered_tasks for task in excluded_tasks)

    def test_delete_dangling_objects_tasks(self):
        schedules = baker.make("django_q.Schedule", _quantity=3)
        registry = TaskRegistry(
            registered_tasks=set(
                baker.make(
                    "django_q_registry.Task",
                    q_schedule=itertools.cycle(schedules),
                    _quantity=len(schedules),
                )
            )
        )
        baker.make("django_q_registry.Task", _quantity=3)

        Task.objects.delete_dangling_objects(registry)

        assert Task.objects.count() == len(schedules)

    def test_delete_dangling_objects_schedules(self):
        schedules = baker.make("django_q.Schedule", _quantity=3)
        registry = TaskRegistry(
            registered_tasks=set(
                baker.make(
                    "django_q_registry.Task",
                    q_schedule=itertools.cycle(schedules),
                    _quantity=len(schedules),
                )
            )
        )
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

        Task.objects.delete_dangling_objects(registry)

        assert Schedule.objects.count() == len(schedules)

    def test_delete_dangling_objects_legacy_schedules(self):
        schedules = baker.make("django_q.Schedule", _quantity=3)
        registry = TaskRegistry(
            registered_tasks=set(
                baker.make(
                    "django_q_registry.Task",
                    q_schedule=itertools.cycle(schedules),
                    _quantity=len(schedules),
                )
            )
        )
        baker.make(
            "django_q.Schedule",
            name=itertools.cycle([f"dangling_schedule{i} - CRON" for i in range(3)]),
            _quantity=3,
        )

        Task.objects.delete_dangling_objects(registry)

        assert Schedule.objects.count() == len(schedules)


class TestTask:
    def test_hash_in_memory(self):
        task = Task(
            name="test",
            func="tests.test_task.test_hash",
            kwargs={"foo": "bar"},
        )
        assert isinstance(hash(task), int)

    def test_hash_in_db(self):
        task = baker.make(
            "django_q_registry.Task",
            name="test",
            func="tests.test_task.test_hash",
            kwargs={"foo": "bar"},
        )
        assert isinstance(hash(task), int)

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
