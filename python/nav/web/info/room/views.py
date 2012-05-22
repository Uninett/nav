from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.models.manage import Room, Netbox

def search(request):
    return render_to_response("info/room/base.html", {}, 
                              context_instance=RequestContext(request))


def roominfo(request, roomid):
    room = Room.objects.get(id=roomid)
    netboxes = room.netbox_set.all().order_by("category", "sysname")

    # Filter interfaces on iftype
    for netbox in netboxes:
        netbox.interfaces = netbox.interface_set.filter(iftype=6).order_by("ifindex")

    return render_to_response("info/room/roominfo.html",
                              {"room": room,
                               "netboxes": netboxes},
                              context_instance=RequestContext(request))

