from django.core.management.base import BaseCommand
from django_q_registry.registry import registry


class Command(BaseCommand):
    help = "Register all tasks in the registry"

    def handle(self, *args, **options):
        registry.register_all()
