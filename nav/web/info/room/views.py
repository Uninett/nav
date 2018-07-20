#
# Copyright (C) 2012-2018 Uninett AS
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
"""Viev functions for the roominfo subsystem"""

import datetime
import logging
import csv

from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Q, Max
from django.http import HttpResponse
from django.shortcuts import (render_to_response, redirect, get_object_or_404,
                              render)
from django.template import RequestContext

from nav.django.decorators import require_admin

from nav.models.manage import Room, Sensor, Interface
from nav.models.rack import (Rack, SensorRackItem, SensorsDiffRackItem,
                             SensorsSumRackItem)
from nav.web.info.forms import SearchForm
from nav.web.info.images.upload import handle_image_upload
from nav.web.utils import create_title
from nav.metrics.data import get_netboxes_availability


CATEGORIES = ("GW", "GSW", "SW", "EDGE")
RACK_LEFT = 0
RACK_CENTER = 1
RACK_RIGHT = 2
COLUMNS = {
    RACK_LEFT: 'left',
    RACK_CENTER: 'center',
    RACK_RIGHT: 'right',
}

_logger = logging.getLogger('nav.web.info.room')


class RoomSearchForm(SearchForm):
    """Searchform for rooms"""
    def __init__(self, *args, **kwargs):
        super(RoomSearchForm, self).__init__(
            *args, form_action='room-search', placeholder='Room', **kwargs)


def get_path():
    """Get the path for this subsystem"""
    return [('Home', '/'), ('Search', reverse('info-search')),
            ('Room', reverse('room-search'))]


def search(request):
    """Controller for searching for rooms"""
    navpath = get_path()

    rooms = Room.objects.none()
    titles = navpath

    if "query" in request.GET:
        searchform = RoomSearchForm(request.GET, auto_id=False)
        if searchform.is_valid():
            titles.append(("Search for %s" % request.GET['query'],))
            rooms = process_searchform(searchform)
            for room in rooms:
                room.netboxes = filter_netboxes(room)
    else:
        searchform = RoomSearchForm()

    return render_to_response("info/room/base.html",
                              {"searchform": searchform,
                               "rooms": rooms,
                               "navpath": navpath,
                               "title": create_title(titles)},
                              context_instance=RequestContext(request))


def process_searchform(form):
    """Find and return rooms based on searchform"""
    query = form.cleaned_data['query']
    if query is None:
        return Room.objects.all()
    else:
        return Room.objects.filter(
            Q(id__icontains=query) |
            Q(description__icontains=query) |
            Q(location__id__icontains=query)
        ).order_by("id")


def filter_netboxes(room):
    """Filter netboxes based on interesting categories"""
    return room.netbox_set.filter(category__in=CATEGORIES)


def roominfo(request, roomid):
    """Controller for displaying roominfo"""
    room = get_object_or_404(Room, id=roomid)
    images = room.image_set.all()
    navpath = get_path() + [(room.id,)]
    room.sorted_data = sorted(room.data.items())
    room.meta_data = get_room_meta(room)
    return render_to_response("info/room/roominfo.html",
                              {"room": room,
                               "navpath": navpath,
                               "title": create_title(navpath),
                               "images": images},
                              context_instance=RequestContext(request))


def get_room_meta(room):
    """Find meta data for the room"""
    room_interfaces = Interface.objects.filter(netbox__room=room)
    return {
        'devices': room.netbox_set.count(),
        'interfaces': room_interfaces.count(),
        'interfaces_with_link': room_interfaces.filter(ifoperstatus=Interface.OPER_UP).count(),
        'trunk_interfaces': room_interfaces.filter(trunk=True).count()
    }


def render_deviceinfo(request, roomid):
    """Controller for rendering device info"""
    room = get_object_or_404(Room, id=roomid)
    all_netboxes = room.netbox_set.select_related(
        'type', 'category', 'organization').order_by('sysname')
    return render(request, 'info/room/roominfo_devices.html', {
        'netboxes': all_netboxes,
        'availabilities': get_netboxes_availability(
            all_netboxes, data_sources=['availability'],
            time_frames=['week', 'month'])
    })


def upload_image(request, roomid):
    """Controller for uploading an image"""

    room = get_object_or_404(Room, pk=roomid)
    navpath = get_path() + [
        (room.id, reverse('room-info', kwargs={'roomid': room.id})),
        ('Edit images',)
    ]

    if request.method == 'POST':
        _logger.debug('Uploading images')
        handle_image_upload(request, room=room)
        return redirect("room-info-upload", roomid=room.id)

    return render_to_response("info/room/upload.html",
                              {"object": room, "room": room, "navpath": navpath,
                               "title": create_title(navpath)},
                              context_instance=RequestContext(request))


def render_netboxes(request, roomid):
    """Controller for displaying the netboxes in the tabbed view"""
    room = get_object_or_404(Room, id=roomid)
    netboxes = filter_netboxes(room).order_by("category", "sysname")

    cam_query = {'last_cam': """SELECT end_time
                            FROM cam
                            WHERE cam.netboxid=interface.netboxid
                              AND cam.ifindex = interface.ifindex
                              AND interface.to_netboxid IS NULL
                            ORDER BY end_time DESC
                            LIMIT 1"""}

    # Filter interfaces on iftype and add fast last_cam lookup
    for netbox in netboxes:
        netbox.interfaces = netbox.interface_set.filter(
            iftype=6).order_by("ifindex").extra(select=cam_query)

    return render_to_response("info/room/netboxview.html",
                              {"netboxes": netboxes,
                               "maxtime": datetime.datetime.max,
                               "room": room},
                              context_instance=RequestContext(request))


def create_csv(request):
    """Create csv-file from form data"""
    roomname = request.REQUEST.get('roomid', 'room').encode('utf-8')
    filename = "{}.csv".format(roomname)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        filename)

    writer = csv.writer(response)
    rows = request.REQUEST.get('rows', '').encode('utf-8')
    for row in rows.splitlines():
        writer.writerow(row.split(';'))
    return response


def render_sensors(request, roomid):
    """Gets the environment devices for a room"""
    room = get_object_or_404(Room, pk=roomid)
    netboxes = room.netbox_set.filter(category='ENV')

    for netbox in netboxes:
        netbox.env_sensors = netbox.sensor_set.filter(
            Q(unit_of_measurement__icontains='celsius') |
            Q(unit_of_measurement__icontains='percent') |
            Q(unit_of_measurement__icontains='degrees') |
            Q(unit_of_measurement__startswith='%'))

    return render(request, 'info/room/roominfo_sensors.html', {
        'netboxes': [n for n in netboxes if n.env_sensors],
        'has_sensors': any([x.get_environment_sensors().count()
                            for x in netboxes])

    })


def create_rack(room, rackname):
    """Creates a rack in a room with a given name"""
    aggregate = Rack.objects.filter(room=room).aggregate(Max('ordering'))
    ordering = (aggregate.get('ordering__max') or 0) + 1
    rack = Rack(room=room, rackname=rackname, ordering=ordering)
    rack.save()
    return rack


@require_admin
def add_rack(request, roomid):
    """Adds a new rack to a room"""
    room = get_object_or_404(Room, pk=roomid)
    rackname = request.POST.get('rackname')
    return render(request, 'info/room/fragment_rack.html', {
        'rack': create_rack(room, rackname),
        'room': room
    })


@require_admin
def remove_rack(request, roomid):
    """Deletes a rack"""
    rack = get_object_or_404(Rack, pk=request.POST.get('rackid'))
    rack.delete()
    return HttpResponse()


@require_admin
def rename_rack(request, roomid, rackid):
    """Renames a rack"""
    rack = get_object_or_404(Rack, pk=rackid)
    newname = request.POST.get('rackname')
    rack.rackname = newname
    rack.save()
    return HttpResponse(newname)


def render_racks(request, roomid):
    """Gets the racks for this room"""
    room = get_object_or_404(Room, pk=roomid)
    background_color_classes = ['bg1', 'bg2', 'bg3', 'bg4', 'bg5']

    context = {
        'room': room,
        'racks': room.rack_set.all().order_by('ordering'),
        'color_classes': background_color_classes
    }
    return render(request, 'info/room/roominfo_racks.html', context)


@require_admin
def render_add_sensor(request, roomid):
    """Controller for rendering the add sensor template"""
    rackid = request.POST.get('rackid')
    column = request.POST.get('column')
    is_pdu = request.POST.get('is_pdu') == 'true'

    room = get_object_or_404(Room, pk=roomid)
    rack = get_object_or_404(Rack, pk=rackid)

    # Filter away already added sensors
    already_used = Rack.objects.get_all_sensor_pks_in_room(room)
    sensors = Sensor.objects.exclude(pk__in=already_used)

    # Sensors that can be choosen for the pdu columns
    pdusensors = sensors.filter(
        netbox__room=room,
        netbox__category='POWER'
    ).select_related('netbox').order_by('netbox__sysname', 'human_readable')

    filteredsensors = pdusensors

    if not is_pdu:
        # All other sensors
        othersensors = sensors.filter(
            netbox__room=room).exclude(
            pk__in=pdusensors).select_related(
            'netbox').order_by('netbox__sysname', 'human_readable')

        filteredsensors = othersensors

    return render(request, 'info/room/fragment_add_rackitem.html', {
        'room': room,
        'rack': rack,
        'sensortype': 'pdu sensor' if is_pdu else 'sensor',
        'sensors': filteredsensors,
        'column': column
    })


@require_admin
def save_sensor(request, roomid):
    rackid = request.POST.get('rackid')
    column = int(request.POST.get('column'))
    get_object_or_404(Room, pk=roomid)
    rack = get_object_or_404(Rack, pk=rackid)
    item_type = request.POST.get('item_type')
    if item_type == "Sensor":
        sensorid = request.POST.get('sensorid')
        sensor = get_object_or_404(Sensor, pk=sensorid)
        item = SensorRackItem(sensor=sensor)
    elif item_type == "SensorsDiff":
        minuendid = request.POST.get('minuendid')
        minuend = get_object_or_404(Sensor, pk=minuendid)
        subtrahendid = request.POST.get('subtrahendid')
        subtrahend = get_object_or_404(Sensor, pk=subtrahendid)
        item = SensorsDiffRackItem(minuend=minuend, subtrahend=subtrahend)
    elif item_type == "SensorsSum":
        sensors = request.POST.getlist('sensors[]')
        sensors = [int(s) for s in sensors if s]
        title = request.POST.get('title')
        item = SensorsSumRackItem(title=title, sensors=sensors)
    try:
        if column == RACK_CENTER:
            rack.add_center_item(item)
            rack.save()
            return render(request, 'info/room/fragment_racksensor.html', {
                'racksensor': item,
                'column': column,
            })
        else:
            if column == RACK_LEFT:
                rack.add_left_item(item)
            else:
                rack.add_right_item(item)
            rack.save()
            return render(request, 'info/room/fragment_rackpdusensor.html', {
                'racksensor': item,
                'column': column,
            })

    except (ValueError, IntegrityError) as error:
        return HttpResponse(error, status=500)


@require_admin
def save_sensor_order(request, roomid):
    """Saves the sensor order for the given racksensors"""
    rackid = request.POST.get('rackid')
    rack = get_object_or_404(Rack, pk=rackid)
    column = int(request.POST.get('column'))
    if column not in COLUMNS:
        return HttpResponse(status=400)
    column = COLUMNS[column]
    items = {item.id: item for item in rack.configuration[column]}
    rack.configuration[column] = [items[int(itemid)] for itemid in
                                  request.POST.getlist('item[]')]
    rack.save()

    return HttpResponse()


@require_admin
def save_rack_order(request, roomid):
    """Saves the rack order for the given racks"""
    for index, rackid in enumerate(request.POST.getlist('rack[]')):
        rack = Rack.objects.get(pk=rackid)
        rack.ordering = index
        rack.save()

    return HttpResponse()


@require_admin
def save_rack_color(request, roomid):
    """Saves the background color for the rack as a class"""
    _room = get_object_or_404(Room, pk=roomid)
    rackid = request.POST.get('rackid')
    rack = get_object_or_404(Rack, pk=rackid)
    rack.configuration['body_class'] = request.POST.get('class')
    rack.save()
    return HttpResponse()


@require_admin
def remove_sensor(request, roomid):
    """Remove a sensor from a rack"""
    rackid = request.POST.get('rackid')
    rack = get_object_or_404(Rack, pk=rackid)
    column = int(request.POST.get('column'))
    itemid = int(request.POST.get('id'))
    if column not in COLUMNS:
        return HttpResponse(status=400)
    column = COLUMNS[column]
    rack.configuration[column] = [item for item in rack.configuration[column]
                                  if item.id != itemid]
    try:
        rack.save()
        return HttpResponse()
    except:
        return HttpResponse(status=500)
