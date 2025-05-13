#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utils for the image upload views"""

import errno
import hashlib
import time
import os
from os.path import exists, join, splitext
from PIL import Image, ImageOps
from django.db.models import Max

THUMBNAILWIDTH = 300  # Maximum width for thumbnail
THUMBNAILHEIGHT = 600  # Maximum height for thumbnail


def get_extension(filename):
    """Get the file extension from a file (with the dot)"""
    return splitext(filename)[-1]


def create_hash(something, salt=False):
    """Create a hash from something, optionally salted with current epoch"""
    data = str(something) + str(time.time()) if salt else something
    try:
        hash_object = hashlib.sha1(data)
    except TypeError:
        hash_object = hashlib.sha1(data.encode('utf-8'))

    return hash_object.hexdigest()


def get_next_priority(obj):
    """Get the next priority value for the images in the room/location"""
    priority = obj.images.all().aggregate(Max('priority'))['priority__max']
    return priority + 1 if priority is not None else 0


def create_image_directory(imagedirectory):
    """Create directory and change permissions"""
    if not exists(imagedirectory):
        try:
            os.makedirs(imagedirectory, mode=0o0755)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(imagedirectory):
                pass
            else:
                raise


def save_image(image, imagefullpath):
    """Save image as a file on the given path
    :type image: django.core.files.uploadedfile.InMemoryUploadedFile
    :type imagefullpath: str
    """
    with open(imagefullpath, 'wb+') as destination:
        for chunk in image.chunks():
            destination.write(chunk)
        os.chmod(imagefullpath, 0o0644)


def save_thumbnail(imagename, imagedirectory, thumb_dir):
    """Save a thumbnail for this image"""
    create_image_directory(thumb_dir)
    image = ImageOps.exif_transpose(Image.open(join(imagedirectory, imagename)))
    image.thumbnail((THUMBNAILWIDTH, THUMBNAILHEIGHT))
    image.save(join(thumb_dir, imagename))
