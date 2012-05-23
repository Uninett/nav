from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.models.manage import Room, Netbox
from nav.web.info.room.forms import SearchForm

def search(request):
    rooms = Room.objects.none()

    if request.method == "GET":
        searchform = SearchForm()
    elif request.method == "POST":
        searchform = SearchForm(request.POST, auto_id=False)
        if searchform.is_valid():
            rooms = process_searchform(searchform)

    return render_to_response("info/room/base.html", 
                              {"searchform": searchform,
                               "rooms": rooms},
                              context_instance=RequestContext(request))

def process_searchform(form):
    query = form.cleaned_data['query']
    return Room.objects.filter(
        Q(id__icontains=query) |
        Q(description__icontains=query)
    )


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

