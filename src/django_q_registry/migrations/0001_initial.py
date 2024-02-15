# Generated by Django 4.2.4 on 2024-02-15 16:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("django_q", "0017_task_cluster_alter"),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("func", models.CharField(max_length=256)),
                ("kwargs", models.JSONField(default=dict)),
                (
                    "q_schedule",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="registered_task",
                        to="django_q.schedule",
                    ),
                ),
            ],
        ),
    ]
