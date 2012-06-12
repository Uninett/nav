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
    rooms = Room.objects.none()

    if request.method == "GET":
        searchform = SearchForm()
    elif request.method == "POST":
        searchform = SearchForm(request.POST, auto_id=False)
        if searchform.is_valid():
            rooms = process_searchform(searchform)
            for room in rooms:
                room.netboxes = filter_netboxes(room)

    return render_to_response("info/room/base.html", 
                              {"searchform": searchform,
                               "rooms": rooms},
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

    netboxes = filter_netboxes(room).order_by("category", "sysname")

    # Filter interfaces on iftype
    for netbox in netboxes:
        netbox.interfaces = netbox.interface_set.filter(iftype=6).order_by("ifindex")

    return render_to_response("info/room/roominfo.html",
                              {"room": room,
                               "all_netboxes": all_netboxes,
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

