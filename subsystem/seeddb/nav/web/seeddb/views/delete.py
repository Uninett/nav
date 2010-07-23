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

def room_delete(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('seeddb-room'))

    rooms = Room.objects.order_by('id').filter(id__in=request.POST.getlist('object'))
    if request.POST.get('confirm'):
        rooms.delete()
        new_message(request._req, "Deleted", Messages.SUCCESS)
        return HttpResponseRedirect(reverse('seeddb-room'))

    cabling_qs = Cabling.objects.filter(room__in=rooms).values('id', 'room')
    netbox_qs = Netbox.objects.filter(room__in=rooms).values('id', 'room', 'sysname')
    cabling = group_query(cabling_qs, 'room')
    netbox = group_query(netbox_qs, 'room')

    objects = []
    errors = False
    for r in rooms:
        object = {
            'object': r,
            'disabled': False,
            'error': [],
        }
        for n in netbox.get(r.id, []):
            errors = True
            object['disabled'] = True
            object['error'].append({
                'message': "Used in netbox",
                'title': n['sysname'],
                'url': reverse('seeddb-netbox-edit', args=(n['id'],)),
            })
        if r.id in cabling and len(cabling[r.id]) > 0:
            object['error'].append("Used in cabling")
            errors = True
        objects.append(object)

    context = {
        'objects': objects,
        'errors': errors,
    }
    return render_to_response('seeddb/delete.html',
        context, RequestContext(request))
