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

from django.views.generic import list_detail
from django.shortcuts import render_to_response as django_render_to_response

from nav.buildconf import VERSION

def render_to_response(cheetah_template_func, template_name, context,
        context_instance=None, path=[('Home', '/')]):

    context['deprecated'] = True
    context['navpath'] = path
    context['title'] = 'NAV'
    context['version'] = VERSION

    return django_render_to_response(
        template_name,
        context,
        context_instance,
    )

def object_list(cheetah_template_func, *args, **kwargs):
    """Mixes Django's generic view object_list with a Cheetah template"""

    # Pop path component
    path = kwargs.pop('path', None)
    try:
        kwargs['extra_context']['deprecated'] = True
        kwargs['extra_context']['title'] = 'NAV'
        kwargs['extra_context']['version'] = VERSION
        if path:
            kwargs['extra_context']['navpath'] = path
    except KeyError:
        pass

    # Pass on call to original object_list view
    return list_detail.object_list(*args, **kwargs)

def object_detail(cheetah_template_func, *args, **kwargs):
    """Mixes Django's generic view object_detail with a Cheetah template"""

    # Pop path component
    path = kwargs.pop('path', None)
    try:
        kwargs['extra_context']['deprecated'] = True
        kwargs['extra_context']['title'] = 'NAV'
        kwargs['extra_context']['version'] = VERSION
        if path:
            kwargs['extra_context']['navpath'] = path
    except KeyError:
        pass

    return list_detail.object_detail(*args, **kwargs)
