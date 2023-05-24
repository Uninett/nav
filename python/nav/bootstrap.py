# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import

from os.path import dirname, realpath
import os
import sys

import django
from django.apps import apps


__all__ = ['bootstrap_django']

RUN = False


def bootstrap_django(caller=None):
    """
    Set up django (especially important: the database connection)

    This is necessary when having standalone Python scripts that use the
    database via the Django model definitions. NAV is older than Django, the
    Django native way is to use management-commands. The Django "manage.py"
    script essentially does this before it runs a command.
    """
    global RUN

    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

    mydir = dirname(dirname(realpath(__file__)))
    sys.path.append(mydir)

    if not RUN and not apps.ready:
        django.setup()
        RUN = True
        return
