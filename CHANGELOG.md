# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project attempts to adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
## [${version}]
### Added - for new features
### Changed - for changes in existing functionality
### Deprecated - for soon-to-be removed features
### Removed - for now removed features
### Fixed - for any bug fixes
### Security - in case of vulnerabilities
[${version}]: https://github.com/westerveltco/django-q-registry/releases/tag/v${version}
-->
## [Unreleased]

## [0.2.0]

### Added

- Refactored the `django_q_registry.registry.Task` dataclass into a `django_q_registry.models.Task` Django model. This should make it more flexible and robust for registering tasks and the associated `django_q.models.Schedule` instances.

### Changed

- Now using [`django-twc-package`](https://github.com/westerveltco/django-twc-package) template for repository and package structure.
- The default for the `Q_REGISTRY["PERIOIDIC_TASK_SUFFIX"]` app setting has been changed from `"- CRON"` to `"- QREGISTRY"`.
- All database logic has been moved from the `TaskRegistry` to the `setup_periodic_tasks` management command.
- GitHub Actions `test` workflow now uses the output of `nox -l --json` to dynamically generate the test matrix.

### Fixed

- Fixed a bug in the hashing of a `Task` where the `hash` function was passed unhashable values (e.g. a `dict`). Thanks to [@Tobi-De](https://github.com/Tobi-De) for the bug report ([#6](https://github.com/westerveltco/django-q-registry/issues/6)).

## [0.1.0]

Initial release!

### Added

- Initial documentation.
- Initial tests.
- Initial CI/CD (GitHub Actions).
- A registry for Django Q2 periodic tasks.
  - `registry.register` function for registering periodic tasks with a convenience decorator `register_task`.
  - A `TASKS` setting for registering periodic tasks from Django settings.
- Autodiscovery of periodic tasks from a Django project's `tasks.py` files.
- A `setup_periodic_tasks` management command for setting up periodic tasks in the Django Q2 broker.

### New Contributors

- Josh Thomas <josh@joshthomas.dev> (maintainer)

[unreleased]: https://github.com/westerveltco/django-q-registry/compare/v0.2.0...HEAD
[0.1.0]: https://github.com/westerveltco/django-q-registry/releases/tag/v0.1.0

[0.2.0]: https://github.com/westerveltco/django-q-registry/releases/tag/v0.2.0
