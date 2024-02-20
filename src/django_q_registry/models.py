from __future__ import annotations

import json
import logging
from typing import Any
from typing import Callable

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django_q.models import Schedule

from django_q_registry.conf import app_settings
from django_q_registry.registry import TaskRegistry

logger = logging.getLogger(__name__)


class TaskQuerySet(models.QuerySet):
    def create_in_memory(
        self, func: Callable[..., Any], kwargs: dict[str, Any]
    ) -> Task:
        """
        Returns a new Task instance with no primary key, for use in `django_q_registry.registry.TaskRegistry`.

        This is to be used when registering a task to the registry, but not yet saving it to the database.
        Useful to avoid the database hit on startup when tasks are actually registered to the `TaskRegistry`,
        as well as the potential for the app registry not being ready yet. Plus, it allows for the `Task`
        object to be hashed and compared for equality to avoid duplicate tasks in the registry and database.

        Args:
            func:
                The function to be called when the task is executed. Corresponds to the `func` argument in
                `django_q.models.Schedule`.
            kwargs:
                The keyword arguments to be passed to `django_q.models.Schedule` when creating a new `Schedule`
                instance for the `Task` instance. Corresponds to the remaining fields in
                `django_q.models.Schedule`. One special case is the `name` field that can be passed in here to
                specify the name of the `Task` and `Schedule` instance. If not passed in, the `name` field
                will be set to the name of the `func`.

                Given the following `kwargs`:

                {
                    "name": "my_task",
                    "repeats": 1,
                    "schedule_type": "D",
                    # ...
                }

                Would result in the following `Task`:`

                Task(
                    name="my_task",
                    func="...",
                    kwargs={
                        "repeats": 1,
                        "schedule_type": "D",
                    },
                )

                Which would then result in the following `Schedule`, once the `Task` is saved to the database:

                Schedule(
                    name="my_task",
                    func="...",
                    repeats=1,
                    schedule_type="D",
                )

        Returns:
            A new `Task` instance with no primary key, to be used later within the
            `django_q_registry.registry.TaskRegistry` to actually create the `Task` instance in the database.
        """

        return Task(
            name=kwargs.pop("name", func.__name__),
            func=f"{func.__module__}.{func.__name__}",
            kwargs=kwargs,
        )

    def create_from_registry(self, registry: TaskRegistry) -> TaskQuerySet:
        """
        Given a `TaskRegistry` that contains a set of in-memory `Task` instances, save them to the database
        and add them to the `TaskRegistry.created_tasks` attribute.

        Note that this method operates on `Task` instances that only exist in-memory and do not exist in the
        database yet. If a `Task` instance is passed in that already exists, it will be logged as an error
        and ignored.

        Duplicates are determined by the `Task` instances' `name`, `func`, and `kwargs` fields. If a `Task`
        instance with the same `name`, `func`, and `kwargs` fields already exists in the database or is
        passed in twice to this method, it will be updated and not duplicated. This means that multiple
        `Tasks` can be registered with the same `name`, `func`, and `kwargs` fields, but only one `Task`
        will be created. See `Task.__eq__` for more information.

        Args:
            registry:
                A TaskRegistry instance containing all of the `Task` instances that are currently registered
                in-memory, but not yet in the database.

        Returns:
            A TaskQuerySet containing all of the `Task` instances that were saved to the database.
        """

        task_objs = []

        for task in registry.registered_tasks:
            if task.pk:
                logger.error(f"Task {task.pk} has already been registered")
                continue

            obj, _ = self.update_or_create(
                name=task.name,
                func=task.func,
                kwargs=task.kwargs,
            )

            if obj.q_schedule is None:
                obj.q_schedule = Schedule.objects.create(
                    **task.to_schedule_dict(),
                )
                obj.save()
            else:
                Schedule.objects.filter(pk=obj.q_schedule.pk).update(
                    **task.to_schedule_dict(),
                )

            task_objs.append(obj)

        return_qs = self.filter(pk__in=[task.pk for task in task_objs])

        registry.update_created_tasks(return_qs)

        return return_qs

    def exclude_registered(self, registry: TaskRegistry) -> TaskQuerySet:
        """
        Get all `Task` instances that are no longer registered in the `TaskRegistry`.

        This method will return all `Task` instances that are not contained in the
        `TaskRegistry.created_tasks` attribute, for use in cleaning up the database of any `Task`
        instances that are no longer registered.

        Args:
            registry:
                A TaskRegistry instance containing all of the `Task` instances that are currently registered
                and in the database.

        Returns:
            A TaskQuerySet containing all of the `Task` instances that are no longer registered in the
            `TaskRegistry`.
        """

        return self.exclude(pk__in=[task.pk for task in registry.created_tasks])

    def delete_dangling_objects(self, registry: TaskRegistry) -> None:
        """
        Delete all `Task` instances from the database and the associated `django_q.models.Schedule` instances
        no longer associated with a `TaskRegistry`.
        """
        to_delete = self.exclude_registered(registry)

        q_schedule_pks = to_delete.values_list("q_schedule", flat=True)

        to_delete.delete()

        suffix = app_settings.PERIODIC_TASK_SUFFIX
        legacy_suffix = " - CRON"

        # clean up legacy registered schedules
        Schedule.objects.filter(name__endswith=legacy_suffix).delete()
        # clean up dangling schedules
        Schedule.objects.filter(
            models.Q(name__endswith=suffix) & models.Q(registered_task__isnull=True)
        ).delete()
        # clean up schedules of tasks that were just deleted
        Schedule.objects.filter(pk__in=q_schedule_pks).delete()


class Task(models.Model):
    q_schedule = models.OneToOneField(
        "django_q.Schedule",
        on_delete=models.SET_NULL,
        null=True,
        related_name="registered_task",
    )
    name = models.CharField(
        max_length=100  # max_length inherited from `django_q.models.Schedule`
    )
    func = models.CharField(
        max_length=256  # max_length inherited from `django_q.models.Schedule`
    )
    kwargs = models.JSONField(default=dict)

    objects = TaskQuerySet.as_manager()

    def __hash__(self) -> int:
        if self.pk is not None:
            return super().__hash__()
        return hash(
            (
                self.name,
                self.func,
                tuple(json.dumps(self.kwargs, cls=DjangoJSONEncoder)),
            )
        )

    def __eq__(self, other) -> bool:
        """
        Compare two `Task` instances for equality.

        If the `Task` exists in the database, then use the default equality comparison which compares the
        primary keys of the `Task` instances.

        Else, compare the `name`, `func`, and `kwargs` fields of the `Task` instances for equality. Two `Task`
        instances are considered equal if they have the same `name`, `func`, and `kwargs` fields.

        So there can be two `Task` instances with the same `name`, `func`, and/or `kwargs` fields, but as long
        as one of those fields is different, they will be considered different `Task` instances.

            >>> task_1 = Task(name="test", func="test_task", kwargs={"foo": "bar"})
            >>> task_2 = Task(name="test", func="test_task", kwargs={"foo": "bar"})
            >>> task_1 == task_2
            True
            >>> diff_name_1 = Task(name="test_1", func="test_task", kwargs={"foo": "bar"})
            >>> diff_name_2 = Task(name="test_2", func="test_task", kwargs={"foo": "bar"})
            >>> diff_name_1 == diff_name_2
            False
            >>> diff_func_1 = Task(name="test", func="test_task_1", kwargs={"foo": "bar"})
            >>> diff_func_2 = Task(name="test", func="test_task_2", kwargs={"foo": "bar"})
            >>> diff_func_1 == diff_func_2
            False
            >>> diff_kwargs_1 = Task(name="test", func="test_task", kwargs={"foo": "bar"})
            >>> diff_kwargs_2 = Task(name="test", func="test_task", kwargs={"baz": "qux"})
            >>> diff_kwargs_1 == diff_kwargs_2
            False

        """

        if self.pk is not None:
            return super().__eq__(other)
        return (
            self.name == other.name
            and self.func == other.func
            and self.kwargs == other.kwargs
        )

    def to_schedule_dict(self) -> dict[str, Any]:
        return {
            "name": f"{self.name}{app_settings.PERIODIC_TASK_SUFFIX}",
            "func": self.func,
            **self.kwargs,
        }
