# Testing recipes — unit, integration, JavaScript, and full tox suite

[private]
default:
    @just --list test --unsorted

# Run full tox test suite
all:
    uv run tox

# Run tox for a specific environment (e.g., unit-py311-django52)
env env:
    uv run tox -e {{ env }}

# Run unit tests directly with pytest (fast inner loop)
quick *args:
    uv run pytest tests/unittests {{ args }}

# Run integration tests directly with pytest
integration *args:
    uv run pytest tests/integration tests/functional {{ args }}

# Run JavaScript tests via tox
js:
    uv run tox -e javascript

# Check for Django deprecation warnings
django-warnings:
    uv run python -Wd -m nav.django.manage check --fail-level=ERROR
