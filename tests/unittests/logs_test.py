"""Tests for nav.logs module"""

import os
from unittest import mock

import pytest

from nav import logs


def test_get_logging_yaml(valid_logging_yaml):
    """Tests the happy path.

    The failure path is covered implicitly by many other tests.
    """
    with mock.patch.dict(os.environ, {"NAV_LOGGING_YAML": str(valid_logging_yaml)}):
        config = logs._get_logging_yaml()
        assert isinstance(config, dict)


@pytest.fixture
def valid_logging_yaml(tmp_path):
    """Provides a minimally valid logging config file in YAML format"""
    filename = tmp_path / "logging.yml"
    with open(filename, "w") as yaml:
        yaml.write(
            """
        version: 1
        """
        )
    yield filename
