# -*- coding: utf-8 -*-
#
# Copyright 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

"""Shortcuts for using Django with NAV and Cheetah"""

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string

def render_to_response(cheetah_template_func, template_name, context,
        context_instance=None):
    """Mixes Django's render_to_response shortcut with a Cheetah template"""

    # Render a Django template with the given context
    rendered = render_to_string(template_name, context, context_instance)

    # Insert the result into content_string in the given Cheetah template
    cheetah_template = cheetah_template_func()
    cheetah_template.content_string = rendered

    # Return a Django HttpResponse with the Cheetah template result
    return HttpResponse(cheetah_template.respond())
