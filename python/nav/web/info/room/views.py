#
# Copyright (C) 2012 (SD -311000) UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#


from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.models.manage import Room, Netbox
from nav.web.info.room.forms import SearchForm


CATEGORIES = ("GW", "GSW", "SW")


def search(request):
    """
    Controller for searching for rooms
    """
    navpath = [('Home', '/'), ('Info', reverse('info-search')), ('Room', reverse('room-search'))]

    rooms = Room.objects.none()

    if "query" in request.GET:
        searchform = SearchForm(request.GET, auto_id=False)
        if searchform.is_valid():
            rooms = process_searchform(searchform)
            for room in rooms:
                room.netboxes = filter_netboxes(room)
    else:
        searchform = SearchForm()

    return render_to_response("info/room/base.html",
                              {"searchform": searchform,
                               "rooms": rooms,
                               "navpath": navpath},
                              context_instance=RequestContext(request))


def process_searchform(form):
    """
    Find and return rooms based on searchform
    """
    query = form.cleaned_data['query']
    if query is None:
        return Room.objects.all()
    else:
        return Room.objects.filter(
            Q(id__icontains=query) |
            Q(description__icontains=query)
        ).order_by("id")


def filter_netboxes(room):
    """
    Filter netboxes based on interesting categories
    """
    return room.netbox_set.filter(category__in=CATEGORIES)


def roominfo(request, roomid):
    """
    Controller for displaying roominfo
    """
    room = Room.objects.get(id=roomid)
    all_netboxes = room.netbox_set.order_by("sysname")
    add_availability(all_netboxes)

    navpath = [('Home', '/'), ('Info', reverse('info-search')), ('Room', reverse('room-search')), (room.id,)]

    return render_to_response("info/room/roominfo.html",
                              {"room": room,
                               "all_netboxes": all_netboxes,
                               "navpath": navpath},
                              context_instance=RequestContext(request))


def netboxes(request, roomid):
    """
    Controller for displaying the netboxes in the tabbed view
    """
    room = Room.objects.get(id=roomid)
    netboxes = filter_netboxes(room).order_by("category", "sysname")

    # Filter interfaces on iftype
    for netbox in netboxes:
        netbox.interfaces = netbox.interface_set.filter(iftype=6).order_by("ifindex")

    return render_to_response("info/room/netboxview.html",
            {"room": room,
             "netboxes": netboxes},
        context_instance=RequestContext(request))



def add_availability(netboxes):
    """
    Add easy to access availabilty for the netboxes
    """
    for netbox in netboxes:
        avail = netbox.get_availability()
        netbox.availability = "N/A"
        try:
            netbox.availability = "%.2f%%" % avail["availability"]["week"]
        except Exception:
            pass

