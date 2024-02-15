from __future__ import annotations

from django.apps import AppConfig


class DjangoQRegistryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_q_registry"
    label = "django_q_registry"
    verbose_name = "Django Q Registry"

    def ready(self):
        from django_q_registry.registry import registry

        registry.autodiscover_tasks()
