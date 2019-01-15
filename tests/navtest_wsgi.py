#
# Copyright (C) 2018 UNINETT
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
"""
WSGI application definition for serving the NAV web application and static
files under gunicorn for the CI test environment.

"""
import os

from whitenoise import WhiteNoise
from nav.wsgi import application

from nav import buildconf

application = WhiteNoise(application, root=buildconf.webrootdir)
# The NAV application links to the documentation static files, but
# they aren't installed under the webroot, so link them in:
application.add_files(buildconf.docdir, prefix='doc/')
