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
"""Viev functions for the roominfo subsystem"""

import hashlib
import logging
import os
from os.path import join, exists
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from nav.models.manage import Room
from nav.models.roommeta import Image
from nav.web.info.room.forms import SearchForm, UploadForm
from nav.web.utils import create_title
from nav.path import localstatedir


CATEGORIES = ("GW", "GSW", "SW", "EDGE")
ROOMIMAGEPATH = join(localstatedir, 'uploads', 'images', 'rooms')
_logger = logging.getLogger('nav.web.info.room')


def get_path():
    return [('Home', '/'), ('Info', reverse('info-search')),
            ('Room', reverse('room-search'))]


def search(request):
    """Controller for searching for rooms"""
    navpath = get_path()

    rooms = Room.objects.none()
    titles = navpath

    if "query" in request.GET:
        searchform = SearchForm(request.GET, auto_id=False)
        if searchform.is_valid():
            titles.append(("Search for %s" % request.GET['query'],))
            rooms = process_searchform(searchform)
            for room in rooms:
                room.netboxes = filter_netboxes(room)
    else:
        searchform = SearchForm()

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
            Q(description__icontains=query)
        ).order_by("id")


def filter_netboxes(room):
    """Filter netboxes based on interesting categories"""
    return room.netbox_set.filter(category__in=CATEGORIES)


def roominfo(request, roomid):
    """Controller for displaying roominfo"""
    room = Room.objects.get(id=roomid)
    all_netboxes = room.netbox_set.order_by("sysname")
    add_availability(all_netboxes)
    images = room.image_set.all()

    navpath = get_path() + [(room.id,)]

    return render_to_response("info/room/roominfo.html",
                              {"room": room,
                               "all_netboxes": all_netboxes,
                               "navpath": navpath,
                               "title": create_title(navpath),
                               "images": images},
                              context_instance=RequestContext(request))


def upload_image(request, roomid):
    """Controller for uploading an image"""

    room = Room.objects.get(pk=roomid)
    navpath = get_path() + [
        (room.id, reverse('room-info', kwargs={'roomid': room.id})),
        ('Edit images',)
    ]

    if request.method == 'POST':
        _logger.debug('Uploading image')

        uploadform = UploadForm(request.POST, request.FILES)
        if uploadform.is_valid():
            image = request.FILES['roomimage'].read()
            imagename = create_hash(image)
            imagedirectory = create_hash(room.id)
            imagedirectorypath = join(ROOMIMAGEPATH, imagedirectory)
            title = (request.POST.get('title') or
                     request.FILES['roomimage'].name)

            create_image_directory(imagedirectorypath)
            save_image(image, join(imagedirectorypath, imagename))

            metaimage = Image(title=title, path=imagedirectory, name=imagename,
                              room=room, priority=room.image_set.all().count())
            metaimage.save()

            return redirect("room-info-upload", roomid=room.id)
    else:
        _logger.debug('Showing upload form')
        uploadform = UploadForm()

    return render_to_response("info/room/upload.html",
                              {"room": room, "navpath": navpath,
                               "title": create_title(navpath),
                               'uploadform': uploadform},
                              context_instance=RequestContext(request))


def create_hash(something):
    """Create a hash from something"""
    return hashlib.sha1(something).hexdigest()


def create_image_directory(imagedirectory):
    if not exists(imagedirectory):
        _logger.debug('Creating directory %s', imagedirectory)
        os.mkdir(imagedirectory)
        os.chmod(imagedirectory, 0755)


def save_image(image, imagefullpath):
    with open(imagefullpath, 'wb+') as destination:
        destination.write(image)
        os.chmod(imagefullpath, 0644)


def update_title(request, roomid):
    if request.method == 'POST':
        imageid = int(request.POST['id'])
        title = request.POST.get('title', '')
        try:
            image = Image.objects.get(pk=imageid)
        except Image.DoesNotExist:
            return HttpResponse(status=500)
        else:
            image.title = title
            image.save()

    return HttpResponse(status=200)


def delete_image(request, roomid):
    if request.method == 'POST':
        imageid = int(request.POST['id'])

        _logger.debug('Deleting image %s', imageid)

        try:
            image = Image.objects.get(pk=imageid)
        except Image.DoesNotExist:
            return HttpResponse(status=500)
        else:
            filepath = join(ROOMIMAGEPATH, image.path, image.name)
            try:
                _logger.debug('Deleting file %s', filepath)
                os.unlink(filepath)
            except OSError:
                return HttpResponse(status=500)

            # Fetch all image instances that uses this image and delete them
            Image.objects.filter(path=image.path, name=image.name).delete()

    return HttpResponse(status=200)


def update_priority(request, roomid):
    """Update the order of image objects"""
    if request.method == 'POST':
        for key, value in request.POST.items():
            _logger.debug('%s=%s', key, value)
            image = Image.objects.get(pk=key)
            image.priority = value
            image.save()

    return HttpResponse(status=200)


def render_netboxes(request, roomid):
    """Controller for displaying the netboxes in the tabbed view"""
    room = Room.objects.get(id=roomid)
    netboxes = filter_netboxes(room).order_by("category", "sysname")

    cam_query = {'last_cam': """SELECT end_time
                            FROM cam
                            WHERE cam.netboxid=interface.netboxid
                              AND cam.ifindex = interface.ifindex
                            ORDER BY end_time DESC
                            LIMIT 1"""}

    # Filter interfaces on iftype and add fast last_cam lookup
    for netbox in netboxes:
        netbox.interfaces = netbox.interface_set.filter(
            iftype=6).order_by("ifindex").extra(select=cam_query)

    return render_to_response("info/room/netboxview.html",
                              {"netboxes": netboxes,
                               "room": room},
                              context_instance=RequestContext(request))


def add_availability(netboxes):
    """Add week availabilty for the netboxes"""
    for netbox in netboxes:
        avail = netbox.get_availability()
        netbox.availability = "N/A"
        try:
            netbox.availability = "%.2f%%" % avail["availability"]["week"]
        except KeyError:
            pass
        except TypeError:
            pass
