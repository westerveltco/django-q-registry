from __future__ import annotations

from django.core.management.base import BaseCommand

from django_q_registry.registry import registry


class Command(BaseCommand):
    help = "Register all tasks in the registry"  # noqa: A003

    def handle(self, *args, **options):  # noqa: ARG002
        registry.register_all()
