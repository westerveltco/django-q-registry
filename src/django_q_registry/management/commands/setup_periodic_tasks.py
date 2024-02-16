from __future__ import annotations

from django.core.management.base import BaseCommand

from django_q_registry.models import Task
from django_q_registry.registry import registry


class Command(BaseCommand):
    help = "Save all registered tasks to the database, create or update the associated schedules, and delete any dangling tasks and schedules."

    def handle(self, *args, **options):  # noqa: ARG002
        Task.objects.create_from_registry(registry)
        Task.objects.delete_dangling_objects(registry)
