from __future__ import annotations

from django_q_registry import __version__


def test_version():
    assert __version__ == "0.3.0"
