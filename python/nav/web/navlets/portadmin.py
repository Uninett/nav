#
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
"""Contains the class for the PortAdmin navlet"""

from nav.web.navlets import Navlet
from nav.web.portadmin.forms import SearchForm


class PortadminNavlet(Navlet):
    """The PortAdmin navlet"""

    title = 'Port Admin'
    description = 'Searches in Port Admin'

    def get_template_basename(self):
        return "portadmin"

    def get_context_data(self, **kwargs):
        context = super(PortadminNavlet, self).get_context_data(**kwargs)
        context['form'] = SearchForm()
        return context
