# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 UNINETT AS
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

"""Shortcuts for using Django with NAV and Cheetah"""

from django.http import HttpResponse
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
