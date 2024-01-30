# django-q-registry

A Django app that provides a registry for Django Q2 periodic tasks.

## Requirements

- Python 3.8, 3.9, 3.10, 3.11, or 3.12
- Django 3.2, 4.2, or 5.0
- Django Q2 1.4.3 or later

## Getting Started

1. Install the package from PyPI:

```bash
python -m pip install django-q-registry
```

2. Add the app to your Django project's `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "django_q_registry",
    ...,
]
```

## Usage

There are three supported ways to register periodic tasks:

1. In a `tasks.py` file in a Django app, using the `@register_task` decorator:

```python
from django.core.mail import send_mail
from django_q_registry import register_task


@register_task(
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
```

2. In a `tasks.py` file in a Django app, using the `registry.register` function directly:

```python
from django.core.mail import send_mail
from django_q_registry.registry import register


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
```

3. In a Django project's `settings.py` file, using the `Q_REGISTRY["TASKS"]` setting:

```python
Q_REGISTRY = {
    "TASKS": [
        {
            "name": "Send periodic test email",
            "func": "django.core.mail.send_mail",
            "kwargs": {
                "subject": "Test email",
                "message": "This is a test email.",
                "from_email": "noreply@example.com",
                "recipient_list": ["janedoe@example.com"],
            },
            "schedule_type": Schedule.CRON,
            # https://crontab.guru/#*/5_*_*_*_*
            "cron": "*/5 * * * *",
        },
    ],
}
