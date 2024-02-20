from __future__ import annotations

import importlib
from dataclasses import dataclass
from dataclasses import field
from functools import wraps
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import cast

from django.conf import settings

from django_q_registry.conf import app_settings

if TYPE_CHECKING:
    from django_q_registry.models import Task
    from django_q_registry.models import TaskQuerySet


@dataclass
class TaskRegistry:
    registered_tasks: set[Task] = field(default_factory=set)
    created_tasks: set[Task] = field(default_factory=set)

    def __post_init__(self):
        self._register_settings()

    def register(self, *args, **kwargs):
        """
        Register a task to be run periodically. Can be used as a function or a decorator.

        This is essentially the same as `django_q.tasks.schedule` but with the added benefit of being able to
        use it as a decorator while also having a registry of all registered tasks.

        If used as a function, the first argument must be the function to be registered.

        The name kwarg is optional, and will default to the name of the function if not provided.

        Example:

            from django.core.mail import send_mail
            from django_q.models import Schedule

            from django_q_registry.registry import TaskRegistry


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

    def _register_task(self, func: Callable[..., Any] | str, **kwargs):
        """
        Register a task to the `registered_tasks` class attribute and return the function. Do not create the
        `Task` object in the database yet, to avoid the database being hit on registration -- plus the
        potential for the app registry not being ready yet.

        The actual `Task` object will be persisted to the database, either created or updated, in the
        `register_all` method which is meant to be manually run as part of the `setup_periodic_tasks`
        management command.
        """
        # imported here to avoid `AppRegistryNotReady` exception, since the `registry` is imported
        # and used in this app config's `ready` method
        from django_q_registry.models import Task

        if not callable(func) and not isinstance(func, str):
            msg = f"{func} is not a string or callable."
            raise TypeError(msg)

        if isinstance(func, str):
            try:
                module_path, function_name = func.rsplit(".", 1)
                module = importlib.import_module(module_path)
                func = getattr(module, function_name)
            except (AttributeError, ImportError, ValueError) as err:
                raise ImportError(f"Could not import {func}.") from err

        # make mypy happy
        func = cast(Callable[..., Any], func)

        self.registered_tasks.add(Task.objects.create_in_memory(func, kwargs))

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

    def update_created_tasks(self, tasks: TaskQuerySet) -> None:
        """
        Update the `created_tasks` class attribute with the tasks that were created in the database.

        Args:
            tasks:
                A queryset of `Task` objects that were created in the database.
        """
        self.created_tasks = set(tasks)


registry = TaskRegistry()
register_task = registry.register
