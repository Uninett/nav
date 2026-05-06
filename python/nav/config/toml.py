#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utility functions for NAV TOML configuration file discovery and parsing."""

try:
    import tomllib
except ImportError:
    # Before Python 3.11
    import tomli as tomllib

import logging
from collections import UserDict
from collections.abc import Mapping
from copy import deepcopy
from typing import Optional

from . import find_config_file


_logger = logging.getLogger(__name__)


class TOMLConfigParser(UserDict):
    """Parse a toml file or section of a toml file into a dict

    The protocol is inspired by but does not blindly mimic NAVConfigParser.
    Writing config files are as of yet not supported.

    TOML as of 1.1 does not support null values so if null is needed define it
    in the DEFAULT_CONFIG.
    """

    SECTION: str = ""  # optional, for parsers specialized for a single section
    DEFAULT_CONFIG: dict = {}
    DEFAULT_CONFIG_FILE: str = ""

    def __init__(
        self, default_config: Optional[dict] = None, default_config_file: str = ""
    ):
        super().__init__()
        if default_config is not None:
            self.DEFAULT_CONFIG = default_config
        # NOTE: a single filename!
        if default_config_file:
            self.DEFAULT_CONFIG_FILE = default_config_file

        ok = self._read(self.DEFAULT_CONFIG_FILE)
        if not ok:
            self.data = self.DEFAULT_CONFIG

    def __getitem__(self, key):
        data = self.data
        if self.SECTION:
            data = self.data.get(self.SECTION, {})
        if key in data:
            return data[key]
        raise KeyError(key)

    def get(self, key, default=None):
        # UserDict.get() uses `key in self` which checks self.data directly,
        # bypassing the SECTION filtering in __getitem__. Use __getitem__ instead.
        try:
            return self[key]
        except KeyError:
            return default

    def read_file(self, fp):
        config = tomllib.load(fp)
        self._merge_with_default(config)
        return self.data

    def read_string(self, s: str, /, *, parse_float=float):
        config = tomllib.loads(s, parse_float)
        self._merge_with_default(config)
        return self.data

    def _merge_with_default(self, configdict):
        self.data = merge_dict_with_defaults(configdict, self.DEFAULT_CONFIG)

    def _read(self, filename):
        fqfn = find_config_file(filename)
        if not fqfn:
            _logger.warning('Config file "%s" not found!', filename)
            return None
        try:
            with open(fqfn, "rb") as F:
                self.read_file(F)
        except OSError:
            return None
        return filename


def merge_dict_with_defaults(data, defaults):
    """Merge the mappings data and defaults, the values in data always wins"""
    if not (isinstance(data, Mapping) and isinstance(defaults, Mapping)):
        return data
    outdict = deepcopy(data)
    for key, value in defaults.items():
        if key not in outdict:
            outdict[key] = value
            continue
        if outdict[key] == value:
            continue
        if not isinstance(value, Mapping):
            continue
        outdict[key] = merge_dict_with_defaults(outdict[key], value)
    return outdict
