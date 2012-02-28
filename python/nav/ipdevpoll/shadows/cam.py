#
# Copyright (C) 2012 UNINETT AS
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
"""cam record storage and handling"""

from nav.models import manage
from nav.ipdevpoll.storage import Shadow, DefaultManager
from .netbox import Netbox

class CamManager(DefaultManager):
    "Manages Cam records"

    def __init__(self, *args, **kwargs):
        super(CamManager).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)


class Cam(Shadow):
    __shadowclass__ = manage.Cam
    manager = CamManager
