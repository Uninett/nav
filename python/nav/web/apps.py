#
# Copyright (C) 2019 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import sys
from django.apps import AppConfig


class NAVWebAppConfig(AppConfig):
    name = 'nav.web'
    verbose_name = 'NAV Main web frontend application'

    def ready(self):
        if 'runserver' not in sys.argv:
            return

        # Initialize logging if running directly inside Django runserver,
        # otherwise, the wsgi module will take care of it.
        from nav.web import loginit
        loginit()
