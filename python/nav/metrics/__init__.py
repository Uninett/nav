# Copyright (C) 2013 Uninett AS
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
"""
This package encompasses all NAV APIs to send and retrieve metrics and
graphs from Graphite.
"""

from nav.config import NAVConfigParser


class GraphiteConfigParser(NAVConfigParser):
    """Parser for NAV's graphite related configuration"""

    DEFAULT_CONFIG_FILES = ['graphite.conf']
    DEFAULT_CONFIG = """
[carbon]
host = 127.0.0.1
port = 2003

[graphiteweb]
base=http://localhost:8000/
format=png
"""


CONFIG = GraphiteConfigParser()
CONFIG.read_all()
