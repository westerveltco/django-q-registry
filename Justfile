set dotenv-load := true

@_default:
  just --list

dev:
  python -m pip install -U pip
  python -m pip install '.[dev]'

test:
  python -m nox --reuse-existing-virtualenvs
