# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

def render_seeddb_list(request, queryset, value_list, labels, edit_url, edit_url_attr='pk', extra_context={}):
    object_list = list()
    query_values = queryset.values('pk', edit_url_attr, *value_list)
    for object in query_values:
        urltitle = object[edit_url_attr]
        row = {
            'pk': object['pk'],
            'url': (urltitle, reverse(edit_url, args=(urltitle,))),
            'values_list': [object[attr] for attr in value_list],
        }
        object_list.append(row)
    info_dict =  {
        'object_list': object_list,
        'labels': labels,
    }
    info_dict.update(extra_context)
    return render_to_response(
        'seeddb/list.html',
        info_dict,
        RequestContext(request)
    )
