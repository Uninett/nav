#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Tests for NAV's configuration file handling (#4132).

NAV reads configuration files as UTF-8 regardless of locale, so the shipped
examples must be valid UTF-8 and the INI/TOML ones must parse cleanly through
NAV's own readers, and the readers themselves must decode as UTF-8 even when the
locale's preferred encoding is not.
"""

import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import nav
from nav.config import getconfig

_ETC_DIR = Path(nav.__file__).resolve().parent / "etc"

# Shipped INI-style configuration files, i.e. the ones NAV parses with a
# configparser-based reader. getconfig() reads them exactly as NAV does in
# production (via open_configfile(), which decodes as UTF-8).
_INI_CONFIG_FILES = [
    "alertengine.conf",
    "alertprofiles/five_periods.conf",
    "alertprofiles/one_period.conf",
    "alertprofiles/three_periods.conf",
    "arnold/arnold.conf",
    "dhcpstats.conf",
    "eventengine.conf",
    "graphite.conf",
    "ipdevpoll.conf",
    "logger.conf",
    "logging.conf",
    "mailin.conf",
    "navstats.conf",
    "netbiostracker.conf",
    "portadmin/portadmin.conf",
    "smsd.conf",
    "snmptrapd.conf",
    "sortedstats.conf",
    "webfront/jwt.conf",
    "webfront/webfront.conf",
]

# Shipped TOML configuration files.
_TOML_CONFIG_FILES = [
    "webfront/authentication.toml",
]


class TestShippedConfigFiles:
    def test_when_walking_shipped_etc_then_every_file_should_be_valid_utf8(self):
        undecodable = []
        for path in _shipped_config_files():
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                undecodable.append(str(path.relative_to(_ETC_DIR)))
        assert not undecodable, f"shipped files are not valid UTF-8: {undecodable}"

    @pytest.mark.parametrize("relative_path", _INI_CONFIG_FILES)
    def test_when_reading_a_shipped_ini_config_then_it_should_parse(
        self, relative_path
    ):
        # Must not raise; an all-comments example legitimately yields no sections.
        getconfig(str(_ETC_DIR / relative_path))

    @pytest.mark.parametrize("relative_path", _TOML_CONFIG_FILES)
    def test_when_reading_a_shipped_toml_config_then_it_should_parse(
        self, relative_path
    ):
        # Must not raise; tomllib mandates UTF-8, so decoding is locale-independent.
        with open(_ETC_DIR / relative_path, "rb") as handle:
            tomllib.load(handle)


class TestRawIniReaderEncoding:
    """Raw configparser-based readers must decode config files as UTF-8
    regardless of the locale's preferred encoding (#4132).
    """

    def test_when_locale_encoding_is_not_utf8_then_logging_conf_reader_should_read_utf8(  # noqa: E501
        self, tmp_path
    ):
        config_file = tmp_path / "logging.conf"
        # The non-ASCII byte lives in a full-line comment, mirroring the stray
        # dash character that triggered #4132 in a shipped config's comment.
        config_file.write_text("[levels]\nroot = INFO\n# a—b\n", encoding="utf-8")

        result = _run_python_in_ascii_locale(
            _READ_LOGGING_CONF_SCRIPT, {"NAV_LOGGING_CONF": str(config_file)}
        )

        if result.returncode == _COULD_NOT_FORCE_ASCII:
            pytest.skip("interpreter could not be forced to a non-UTF-8 locale")
        assert result.returncode == 0, result.stderr


def _shipped_config_files():
    """Yield every shipped file under etc/, minus backups and hidden files."""
    for path in sorted(_ETC_DIR.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.name.startswith(".") or path.name.endswith("~"):
            continue
        yield path


# The regression is only observable when the interpreter's default encoding is
# not UTF-8, and that cannot be changed once the process has started. So we read
# the config file in a child interpreter whose locale is forced to plain ASCII.

_COULD_NOT_FORCE_ASCII = 99

_READ_LOGGING_CONF_SCRIPT = """
import locale
import sys

if "utf" in locale.getpreferredencoding(False).lower().replace("-", ""):
    sys.exit({skip})

from nav.logs import _get_logging_conf

config = _get_logging_conf()
assert config.get("levels", "root") == "INFO", dict(config["levels"])
""".format(skip=_COULD_NOT_FORCE_ASCII)


def _run_python_in_ascii_locale(script, extra_env):
    env = {
        **os.environ,
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONUTF8": "0",
        "PYTHONCOERCECLOCALE": "0",
        **extra_env,
    }
    return subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
