# -*- coding: utf-8 -*-
#
# Copyright 2007, 2008 UNINETT AS
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

__copyright__ = "Copyright 2007, 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.generic import list_detail

def _cheetah_render(cheetah_template_func, rendered_by_django, path=[]):
    """Inserts a rendered template from Django into a Cheetah template"""

    # Insert the result into content_string in the given Cheetah template
    cheetah_template = cheetah_template_func()
    # Make sure we don't mix unicode into the Cheetah template, which
    # will cause UnicodeDecodeErrors (legacy code inserts utf-8
    # encoded strings)
    if isinstance(rendered_by_django, unicode):
        rendered_by_django = rendered_by_django.encode('utf-8')
    cheetah_template.content_string = rendered_by_django

    # Insert path into cheetah
    if path:
        # Same unicode fixing as above, only for the path this time
        for i, path_part in enumerate(path):
            # Path_part is a tuple with the title of the link in position 0 and
            # the url itself in position 1
            if isinstance(path_part[0], unicode):
                path[i] = (path_part[0].encode('utf-8'), path_part[1])

        cheetah_template.path = path

    # Return a Django HttpResponse with the Cheetah template result
    return HttpResponse(cheetah_template.respond())

def render_to_response(cheetah_template_func, template_name, context,
        context_instance=None, path=[]):
    """Mixes Django's render_to_response shortcut with a Cheetah template"""

    # Render a Django template with the given context
    rendered = render_to_string(template_name, context, context_instance)

    # Pass it on to the Cheetah template
    return _cheetah_render(cheetah_template_func, rendered, path)

def object_list(cheetah_template_func, *args, **kwargs):
    """Mixes Django's generic view object_list with a Cheetah template"""

    # Pop path component
    path = kwargs.pop('path', None)

    # Pass on call to original object_list view
    response = list_detail.object_list(*args, **kwargs)

    # Get rendered template from the response object
    rendered = response.content

    # Pass it on to the Cheetah template
    return _cheetah_render(cheetah_template_func, rendered, path)

def object_detail(cheetah_template_func, *args, **kwargs):
    """Mixes Django's generic view object_detail with a Cheetah template"""

    # Pop path component
    path = kwargs.pop('path', None)

    # Pass on call to original object_detail view
    response = list_detail.object_detail(*args, **kwargs)

    # Get rendered template from the response object
    rendered = response.content

    # Pass it on to the Cheetah template
    return _cheetah_render(cheetah_template_func, rendered, path)
