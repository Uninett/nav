#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module comment"""

import os

from nav.buildconf import sysconfdir
from nav.web.navlets import Navlet
from nav.web.webfront.utils import quick_read

WEBCONF_DIR_PATH = os.path.join(sysconfdir, "webfront")
WELCOME_ANONYMOUS_PATH = os.path.join(WEBCONF_DIR_PATH,
                                      "welcome-anonymous.txt")
WELCOME_REGISTERED_PATH = os.path.join(WEBCONF_DIR_PATH,
                                       "welcome-registered.txt")


class WelcomeNavlet(Navlet):
    """A navlet that displays welcome information to the user"""
    title = "Site welcome"
    description = "Displays welcome messages from the site administrators"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.account.is_default_account():
            welcome = quick_read(WELCOME_ANONYMOUS_PATH)
        else:
            welcome = quick_read(WELCOME_REGISTERED_PATH)

        context['welcome'] = welcome

        return self.render_to_response(context)

    def get_template_basename(self):
        return "welcome"
