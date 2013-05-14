#
# Copyright (C) 2013 UNINETT AS
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
"""Contains class based views representing as navlets"""

NAVLET_MODE_VIEW = 'VIEW'
NAVLET_MODE_EDIT = 'EDIT'

import simplejson
from django.conf import settings
from django.http import HttpResponse
from django.views.generic.base import TemplateView


class Navlet(TemplateView):
    """Base class for navlets"""

    title = 'Navlet'

    def get_template_names(self):
        """Get template name based on navlet mode"""
        mode = self.request.GET.get('mode', NAVLET_MODE_VIEW)
        if mode == NAVLET_MODE_VIEW:
            return 'navlets/%s_view.html' % self.base
        elif mode == NAVLET_MODE_EDIT:
            return 'navlets/%s_edit.html' % self.base
        else:
            return 'navlets/%s_view.html' % self.base

    def get_context_data(self, **kwargs):
        context = super(Navlet, self).get_context_data(**kwargs)
        context['navlet'] = self
        return context


def list_navlets(request):
    navlets = []
    for navletmodule in settings.NAVLETS:
        lastmod, clsname = navletmodule.split('.')[-2:]
        module = __import__(navletmodule[:navletmodule.rfind('.')],
                            fromlist=[lastmod])
        navlets.append(getattr(module, clsname))

    return HttpResponse(simplejson.dumps([n.__name__ for n in navlets]))


def get_user_navlets(request, user):
    pass


def add_navlet_to_user(request, user, navlet):
    pass


def remove_navlet_from_user(request, user, navlet):
    pass
