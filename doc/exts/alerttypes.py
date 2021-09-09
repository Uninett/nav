#!/usr/bin/env python3
#
# Copyright (C) 2021 Uninett AS
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
"""This is not really a Sphinx extension, but a tool to autogenerate the reference
documentation for NAV's event- and alert type hierarchy.

It should only be necessary to re-run this in the event of changes to the supported
event/alert types, or in the templates used to generate this doc.
"""
import os

from jinja2 import FileSystemLoader, Environment  # Jinja is a sub-dependency of Sphinx

from nav.bootstrap import bootstrap_django

bootstrap_django(__name__)


from nav.models.event import EventType, AlertType


def main():
    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template('alerttypes.rst.j2')

    types = [
        (eventtype, AlertType.objects.filter(event_type=eventtype))
        for eventtype in EventType.objects.all()
    ]
    print(template.render(types=types))


if __name__ == '__main__':
    main()
