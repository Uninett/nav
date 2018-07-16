# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import traceback

from django.template import loader, Context, RequestContext
from django.http import HttpResponseServerError


def custom_500(request):
    """ View that renders the HTTP 500 template and passes the exception """

    template = loader.get_template('500.html')

    type, value, tb = sys.exc_info()

    return HttpResponseServerError(template.render(Context({
        'type': type.__name__,
        'value': value,
        'traceback': traceback.format_exception(type, value, tb)
        }, RequestContext(request))))
