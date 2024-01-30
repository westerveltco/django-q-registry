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

[unreleased]: https://github.com/westerveltco/django-q-registry/compare/v0.1.0...HEAD
