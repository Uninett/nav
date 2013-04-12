#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utils for the info room views"""
import hashlib
import os
from os.path import exists
from django.db.models import Max


def get_extension(filename):
    """Get the file extension from a file (with the dot)"""
    try:
        return filename[filename.rindex('.'):]
    except ValueError:
        return ""


def create_hash(something):
    """Create a hash from something"""
    return hashlib.sha1(something).hexdigest()


def get_highest_priority(room):
    """Get the highest priority value for the images in this room"""
    return room.image_set.all().aggregate(Max('priority'))['priority__max']


def create_image_directory(imagedirectory):
    """Create directory and change permissions"""
    if not exists(imagedirectory):
        os.mkdir(imagedirectory)
        os.chmod(imagedirectory, 0755)


def save_image(image, imagefullpath):
    """Save image as a file on the given path"""
    with open(imagefullpath, 'wb+') as destination:
        destination.write(image)
        os.chmod(imagefullpath, 0644)
