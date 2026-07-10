import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase

import pytest

from nav.config import _config_resource_walk, find_config_file, get_config_locations


class TestConfigResourceWalk(TestCase):
    def test_should_read_relative_paths_as_strings_from_nav_package_and_return_a_long_list_of_strings(  # noqa: E501
        self,
    ):
        # result should be many, many relative paths as strings
        result = tuple(_config_resource_walk())  # generator
        self.assertTrue(len(result) > 20)
        for relpath in result:
            self.assertIsInstance(relpath, str)
            self.assertFalse(relpath.startswith("/"))


class TestNavConfigDir:
    def test_get_config_locations_should_include_nav_config_dir_first_when_set(
        self, tmp_path_factory, monkeypatch
    ):
        """Test that NAV_CONFIG_DIR appears first in config locations when set"""
        tmpdir = tmp_path_factory.mktemp("foo")
        monkeypatch.setenv("NAV_CONFIG_DIR", str(tmpdir))

        first_location = next(get_config_locations())
        assert first_location == Path(tmpdir)

    def test_get_config_locations_should_work_without_nav_config_dir(self, monkeypatch):
        """Test that config locations work normally when NAV_CONFIG_DIR is not set"""
        # Ensure NAV_CONFIG_DIR is not set
        monkeypatch.delenv("NAV_CONFIG_DIR", raising=False)

        locations = list(get_config_locations())
        # Should have some default locations
        assert len(locations) > 0
        # All should be Path objects
        for location in locations:
            assert isinstance(location, Path)

    def test_find_config_file_should_find_file_in_nav_config_dir(
        self, tmp_path_factory, monkeypatch
    ):
        """Test that find_config_file finds files in NAV_CONFIG_DIR when set"""
        tmpdir = tmp_path_factory.mktemp("foo")
        # Create a test config file
        test_file = Path(tmpdir) / "test.conf"
        test_file.write_text("[test]\nvalue=true\n")

        # Set NAV_CONFIG_DIR
        monkeypatch.setenv("NAV_CONFIG_DIR", str(tmpdir))

        # Should find our test file
        found_path = find_config_file("test.conf")
        assert found_path == str(test_file)

    def test_find_config_file_should_skip_permission_errors(
        self, tmp_path_factory, monkeypatch
    ):
        # Create two temporary directories
        inaccessible_dir = tmp_path_factory.mktemp("inaccessible")
        accessible_dir = tmp_path_factory.mktemp("accessible")

        # Create the config file only in the accessible directory
        test_file = accessible_dir / "test.conf"
        test_file.write_text("[test]\nvalue=true\n")

        # Mock get_config_locations to return our directories in order
        def mock_get_config_locations():
            # Create a mock Path that raises PermissionError on exists()
            class InaccessiblePath:
                def __init__(self, path):
                    self._path = path

                def __truediv__(self, other):
                    return InaccessiblePath(self._path / other)

                def exists(self):
                    raise PermissionError("Permission denied")

            yield InaccessiblePath(inaccessible_dir)
            yield accessible_dir

        monkeypatch.setattr(
            "nav.config.get_config_locations", mock_get_config_locations
        )

        # Should still find the file in the accessible directory
        found_path = find_config_file("test.conf")
        assert found_path == str(test_file)

    def test_when_all_config_locations_are_inaccessible_then_find_config_file_should_return_none(  # noqa: E501
        self, monkeypatch
    ):
        def mock_get_config_locations():
            class InaccessiblePath:
                def __init__(self, name):
                    self._name = name

                def __truediv__(self, other):
                    return InaccessiblePath(f"{self._name}/{other}")

                def exists(self):
                    raise PermissionError("Permission denied")

            yield InaccessiblePath("/fake/path1")
            yield InaccessiblePath("/fake/path2")

        monkeypatch.setattr(
            "nav.config.get_config_locations", mock_get_config_locations
        )

        found_path = find_config_file("nonexistent.conf")
        assert found_path is None


class TestConfigFileEncoding:
    """#4132: config files must be read as UTF-8 regardless of the locale's
    preferred encoding.
    """

    def test_when_locale_encoding_is_not_utf8_then_navconfigparser_should_still_read_utf8_files(  # noqa: E501
        self, tmp_path
    ):
        config_file = tmp_path / "utf8.conf"
        config_file.write_text("[section]\nkey = a—b\n", encoding="utf-8")

        result = _run_in_ascii_locale(_READ_UTF8_CONFIG_SCRIPT, config_dir=tmp_path)

        if result.returncode == _COULD_NOT_FORCE_ASCII:
            pytest.skip("interpreter could not be forced to a non-UTF-8 locale")
        assert result.returncode == 0, result.stderr


# The regression is only observable when the interpreter's default encoding is
# not UTF-8, and that cannot be changed once the process has started. So we read
# the config file in a child interpreter whose locale is forced to plain ASCII.

_COULD_NOT_FORCE_ASCII = 99

_READ_UTF8_CONFIG_SCRIPT = f"""
import locale
import sys

from nav.config import NAVConfigParser

if "utf" in locale.getpreferredencoding(False).lower().replace("-", ""):
    sys.exit({_COULD_NOT_FORCE_ASCII})

parser = NAVConfigParser(default_config="", default_config_files=("utf8.conf",))
expected = "a" + chr(0x2014) + "b"
assert parser.get("section", "key") == expected, parser.get("section", "key")
"""


def _run_in_ascii_locale(script, config_dir):
    env = {
        **os.environ,
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONUTF8": "0",
        "PYTHONCOERCECLOCALE": "0",
        "NAV_CONFIG_DIR": str(config_dir),
    }
    return subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
