from __future__ import annotations

import pytest
from django_q.models import Schedule
from model_bakery import baker

from django_q_registry.models import Task

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

    def test_register(self):
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

        registered_tasks = Task.objects.register(tasks)

        assert len(registered_tasks) == 9

    def test_register_existing_task(self, caplog):
        existing_task = baker.make("django_q_registry.Task")

        with caplog.at_level("ERROR"):
            Task.objects.register([existing_task])

        assert f"Task {existing_task.pk} has already been registered" in caplog.text

    def test_register_existing_task_with_new_task(self, caplog):
        new_task = baker.prepare("django_q_registry.Task", name="new_task")
        existing_task = baker.make("django_q_registry.Task", name="existing_task")

        with caplog.at_level("ERROR"):
            Task.objects.register([new_task, existing_task])

        assert new_task in Task.objects.all()
        assert f"Task {existing_task.pk} has already been registered" in caplog.text

    def test_exclude_registered(self):
        tasks = baker.make("django_q_registry.Task", _quantity=3)

        registered_tasks = Task.objects.filter(pk__in=[task.pk for task in tasks])
        unregistered_tasks = Task.objects.exclude_registered(registered_tasks)

        assert unregistered_tasks.count() == 0

    def test_exclude_registered_with_unregistered_tasks(self):
        tasks = baker.make("django_q_registry.Task", _quantity=3)

        registered_tasks = Task.objects.filter(pk__in=[tasks[0].pk])
        unregistered_tasks = Task.objects.exclude_registered(registered_tasks)

        assert unregistered_tasks.count() == 2

    def test_unregister(self):
        baker.make(
            "django_q.Schedule",
            registered_task=baker.make("django_q_registry.Task"),
            _quantity=3,
        )

        Task.objects.unregister()

        assert Task.objects.count() == 0

    def test_related_field_funkiness(self):
        task = baker.make("django_q_registry.Task")

        assert task.q_schedule is None

        schedule = baker.make("django_q.Schedule", registered_task=task)

        assert Schedule.objects.all().count() == 1
        assert Schedule.objects.first() == schedule

        # this works
        assert task.q_schedule == schedule
        # this doesn't?
        assert Task.objects.first().q_schedule == schedule

        # this works
        assert schedule.registered_task == task
        # this doesn't?
        assert Schedule.objects.first().registered_task == task

        # neither of these work
        assert Schedule.objects.get(registered_task=task) == schedule
        assert Schedule.objects.filter(registered_task__isnull=False).count() == 1

    # def test_unregister_with_registered_tasks(self):
    #     schedule_with_registered_task = baker.make(
    #         "django_q.Schedule",
    #         name=f"registered_schedule{app_settings.PERIODIC_TASK_SUFFIX}",
    #         registered_task=baker.make("django_q_registry.Task"),
    #     )
    #     schedule_with_unregistered_task = baker.make(
    #         "django_q.Schedule",
    #         name=f"unregistered_schedule{app_settings.PERIODIC_TASK_SUFFIX}",
    #         registered_task=None,
    #     )
    #     schedule_with_legacy_suffix = baker.make(
    #         "django_q.Schedule",
    #         name="registered_schedule - CRON",
    #     )
    #     unmanaged_schedule = baker.make("django_q.Schedule")
    #
    #     registered_tasks = Task.objects.filter(
    #         pk__in=[schedule_with_registered_task.registered_task.pk]
    #     )
    #
    #     Task.objects.exclude_registered(registered_tasks).unregister()
    #
    #     schedules = Schedule.objects.all()
    #
    #     assert schedules.count() == 2
    #
    #     assert schedule_with_registered_task in schedules
    #     assert unmanaged_schedule in schedules
    #
    #     assert schedule_with_unregistered_task not in schedules
    #     assert schedule_with_legacy_suffix not in schedules


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
