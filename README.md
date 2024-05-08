# django-q-registry

[![PyPI](https://img.shields.io/pypi/v/django-q-registry)](https://pypi.org/project/django-q-registry/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-q-registry)
![Django Version](https://img.shields.io/badge/django-4.2%20%7C%205.0-%2344B78B?labelColor=%23092E20)
<!-- https://shields.io/badges -->
<!-- django-4.2 | 5.0-#44B78B -->
<!-- labelColor=%23092E20 -->

A Django app to register periodic Django Q tasks.

## Requirements

- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Django 4.2, 5.0
- Django Q2 1.4.3+
  - This package has only been tested with the Django ORM broker.

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

### Registering Periodic Tasks

There are three supported ways to register periodic tasks:

1. In a `tasks.py` file in a Django app, using the `@register_task` decorator:

   ```python
   # tasks.py
   from django.core.mail import send_mail
   from django_q.models import Schedule
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
   # tasks.py
   from django.core.mail import send_mail
   from django_q.models import Schedule
   from django_q_registry.registry import registry


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
   # settings.py
   from django_q.models import Schedule


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
   ```

### Setting up Periodic Tasks in Production

At some point in your project's deployment process, run the `setup_periodic_tasks` management command:

```bash
python manage.py migrate
python manage.py setup_periodic_tasks
```

This command automatically registers periodic tasks from `tasks.py` files in Django apps, and from the `Q_REGISTRY["TASKS"]` setting. It also cleans up any periodic tasks that are no longer registered.

## Documentation

Please refer to the [documentation](https://django-q-registry.westervelt.dev/) for more information.

## License

`django-q-registry` is licensed under the MIT license. See the [`LICENSE`](LICENSE) file for more information.
