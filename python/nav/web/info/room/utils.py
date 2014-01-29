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
import time
import os
from os.path import exists, join, splitext
from PIL import Image
from django.db.models import Max

THUMBNAILWIDTH = 300  # Maximum width for thumbnail
THUMBNAILHEIGHT = 600  # Maximum height for thumbnail


def get_extension(filename):
    """Get the file extension from a file (with the dot)"""
    return splitext(filename)[-1]


def create_hash(something, salt=False):
    """Create a hash from something, optionally salted with current epoch"""
    data = something + str(time.time()) if salt else something
    try:
        hash_object = hashlib.sha1(data)
    except UnicodeEncodeError:
        hash_object = hashlib.sha1(data.encode('utf-8'))

    return hash_object.hexdigest()


def get_next_priority(room):
    """Get the next priority value for the images in this room"""
    priority = room.image_set.all().aggregate(Max('priority'))['priority__max']
    return priority + 1 if priority is not None else 0


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


def save_thumbnail(imagename, imagedirectory, thumb_dir):
    """Save a thumbnail for this image"""
    create_image_directory(thumb_dir)
    image = Image.open(join(imagedirectory, imagename))
    image.thumbnail((THUMBNAILWIDTH, THUMBNAILHEIGHT))
    image.save(join(thumb_dir, imagename))
