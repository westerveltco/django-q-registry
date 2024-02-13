from __future__ import annotations

import json
from typing import Any
from typing import Callable
from typing import Iterable

from django.db import models
from django_q.models import Schedule

from django_q_registry.conf import app_settings


class TaskQuerySet(models.QuerySet):
    def create_in_memory(self, func: Callable, kwargs: dict[str, Any]) -> Task:
        """
        Returns a new Task instance with no primary key, for use in `django_q_registry.TaskRegistry`.

        This is to be used when registering a task to the registry, but not yet saving it to the database.
        Useful to avoid the database hit on startup when tasks are actually registered to the `TaskRegistry`,
        as well as the potential for the app registry not being ready yet. Plus, it allows for the `Task`
        object to be hashed and compared for equality to avoid duplicate tasks in the registry.
        """
        return Task(
            name=kwargs.pop("name", func.__name__),
            func=f"{func.__module__}.{func.__name__}",
            kwargs=kwargs,
        )

    def register_tasks(self, tasks: Iterable[Task]) -> list[int]:
        registered_pks = []
        for task in tasks:
            obj, _, _ = self.register_task(task)
            registered_pks.append(obj.pk)
        return registered_pks

    def register_task(self, task: Task) -> tuple[Task, bool, bool]:
        if task.pk:
            msg = f"Task {task.pk} has already been registered"
            raise ValueError(msg)

        obj, created = self.model.objects.update_or_create(
            name=f"{task.name}",
            defaults={
                "func": task.func,
                "kwargs": task.kwargs,
            },
        )

        q_schedule_created = False
        if obj.q_schedule is None:
            obj.q_schedule = Schedule.objects.create(
                **task.to_schedule_dict(),
            )
            obj.save()
            q_schedule_created = True
        else:
            Schedule.objects.filter(pk=obj.q_schedule.pk).update(
                **task.to_schedule_dict(),
            )

        return obj, created, q_schedule_created

    def unregister_tasks(self) -> None:
        q_schedule_pks = self.values_list("q_schedule", flat=True)

        self.delete()

        Schedule.objects.filter(pk__in=q_schedule_pks).delete()


class Task(models.Model):
    q_schedule = models.OneToOneField(
        "django_q.Schedule",
        on_delete=models.PROTECT,
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
        return hash((self.name, self.func, tuple(json.dumps(self.kwargs))))

    def __eq__(self, other) -> bool:
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
