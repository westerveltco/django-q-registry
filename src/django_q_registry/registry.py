from __future__ import annotations

import importlib
from dataclasses import dataclass
from dataclasses import field
from functools import wraps
from typing import Any
from typing import Callable

from django.conf import settings

from django_q_registry.conf import app_settings


@dataclass
class Task:
    name: str
    func: str
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.name, self.func, tuple(self.kwargs.items())))

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.func == other.func and self.kwargs == other.kwargs

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "func": self.func,
            **self.kwargs,
        }


@dataclass
class TaskRegistry:
    registered_tasks: set[Task] = field(default_factory=set)

    def __post_init__(self):
        self._register_settings()

    def __iter__(self):
        for registered_task in self.registered_tasks:
            yield registered_task.to_dict()

    def register(self, *args, **kwargs):
        """
        Register a task to be run periodically. Can be used as a function or a decorator.

        This is essentially the same as `django_q.tasks.schedule` but with the added benefit of
        being able to use it as a decorator while also having a registry of all registered tasks.

        If used as a function, the first argument must be the function to be registered.

        The name kwarg is optional, and will default to the name of the function if not provided.

        Example::

            from django.core.mail import send_mail
            from django_q.models import Schedule

            from cms.tasks.registry import TaskRegistry

            registry = TaskRegistry()
            @registry.register(
                name="Send periodic test email",
                schedule_type=Schedule.CRON,
                # https://crontab.guru/#*/5_*_*_*_*
                cron="*/5 * * * *",
            )
            def send_test_email():
                send_mail(
                    subject="Test email",
                    message="This is a test email.",
                    from_email="noreply@example.com",
                    recipient_list=["johndoe@example.com"],
                )

            # or

            registry.register(
                send_mail,
                name="Send periodic test email",
                kwargs={
                    "subject": "Test email",
                    "message": "This is a test email.",
                    "from_email": "noreply@example.com",
                    "recipient_list": ["janedoe@example.com"],
                },
                schedule_type=Schedule.CRON,
                # https://crontab.guru/#*/5_*_*_*_*
                cron="*/5 * * * *",
            )
        """
        if len(args) == 1 and callable(args[0]):
            return self._register_task(args[0], **kwargs)
        else:
            return self._register_decorator(**kwargs)

    def _register_decorator(self, **kwargs):
        def decorator(func: Callable):
            self._register_task(func, **kwargs)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def _register_settings(self):
        for task_dict in app_settings.TASKS:
            self._register_task(
                func=task_dict.pop("func"),
                **task_dict,
            )

    def _register_task(self, func: Callable | str, **kwargs):
        if isinstance(func, str):
            module_path, function_name = func.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)
        if not callable(func):
            msg = f"{func} is not callable."
            raise TypeError(msg)
        self.registered_tasks.add(
            Task(
                name=kwargs.pop("name", func.__name__),
                func=f"{func.__module__}.{func.__name__}",
                kwargs=kwargs,
            )
        )

        return func

    def autodiscover_tasks(self):
        """
        Autodiscover tasks from all apps in INSTALLED_APPS.

        This is a simplified version of Celery's autodiscover_tasks function.
        """
        for app_name in settings.INSTALLED_APPS:
            tasks_module = f"{app_name}.tasks"
            try:
                importlib.import_module(tasks_module)
            except ImportError:
                continue

    def register_all(self):
        """
        Create or update all registered tasks in the database, deleting any tasks that
        are no longer registered.

        We make sure to suffix the name of the task with PERIODIC_TASK_SUFFIX (default: " - CRON")
        so that we can easily identify which tasks are periodic tasks. This is useful to
        avoid accidentally deleting scheduled tasks that are not periodic tasks.
        """
        from django_q.models import Schedule

        suffix = app_settings.PERIODIC_TASK_SUFFIX

        orm_tasks = []
        for task in self:
            obj, _ = Schedule.objects.update_or_create(
                name=f"{task.pop('name')}{suffix}",
                defaults=task,
            )
            orm_tasks.append(obj.pk)

        Schedule.objects.exclude(pk__in=orm_tasks).filter(name__endswith=suffix).delete()


registry = TaskRegistry()
register_task = registry.register
