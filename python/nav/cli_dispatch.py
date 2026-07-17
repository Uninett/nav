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
"""Shared console-script entry point for NAV's Django-dependent CLI tools.

NAV predates Django, and many of its command line tools are standalone
scripts that use Django's ORM without being management commands. They
therefore need Django bootstrapped (DJANGO_SETTINGS_MODULE set and
django.setup() called) before anything of theirs that touches the ORM gets
imported - the same problem manage.py solves for management commands.

Every such command's pyproject.toml entry, under [project.scripts], points
here instead of at its own implementing module. This function bootstraps
Django, then looks up and calls the real implementation via the
"nav.cli_commands" entry-point group (see pyproject.toml), based on which
command name this process was invoked as. Because bootstrapping happens
before the implementing module is ever imported, that module's own
top-level imports never need to work around Django not being configured
yet.
"""

import os
import sys
from importlib.metadata import entry_points

from nav.bootstrap import bootstrap_django


def main():
    """Bootstraps Django, then dispatches to the command this was installed as"""
    bootstrap_django()

    command_name = os.path.basename(sys.argv[0])
    try:
        (command,) = entry_points(group="nav.cli_commands", name=command_name)
    except ValueError:
        sys.exit(
            f"{command_name!r} is not a recognized NAV command "
            f"(see the nav.cli_commands entry points in pyproject.toml)"
        )
    return command.load()()
