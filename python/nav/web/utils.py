#
# Copyright (C) 2012 (SD -311000) Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utils for views"""
import base64
import io
import os
from typing import Dict, List

from django.http import HttpResponse
from django.views.generic.list import ListView

import qrcode
from PIL import ImageDraw, ImageFont
import qrcode.image.pil


def get_navpath_root():
    """Returns the default navpath root

    To be used in the navpath argument to the base template
    navpath = [get_navpath_root(), ('Tool', )]
    """
    return 'Home', '/'


def create_title(navpath):
    """Create title from navpath (or any other array of tuples)"""
    return " - ".join([x[0] for x in navpath])


class SubListView(ListView):
    """Subclass of the generic list ListView to allow extra context"""

    extra_context = {}

    def get_context_data(self, *args, **kwargs):
        context = super(SubListView, self).get_context_data(*args, **kwargs)
        context.update(self.extra_context)
        return context


def require_param(parameter):
    """A decorator for requiring parameters

    Will check both GET and POST querydict for the parameter.
    """

    # pylint: disable=missing-docstring
    def wrap(func):
        def wrapper(request, *args, **kwargs):
            if parameter in request.GET or parameter in request.POST:
                return func(request, *args, **kwargs)
            else:
                return HttpResponse(
                    "Missing parameter {}".format(parameter), status=400
                )

        return wrapper

    return wrap


def generate_qr_code(url: str, caption: str = "") -> io.BytesIO:
    """
    Generate a QR code from a given url, and, if given, adds a caption to it

    Returns the generated image as a bytes buffer
    """
    # Creating QR code
    qr = qrcode.QRCode(box_size=10)
    qr.add_data(url)
    img = qr.make_image()
    draw = ImageDraw.Draw(img)

    # Adding caption
    if caption:
        img_width, img_height = img.size
        font_path = os.path.join(os.path.dirname(__file__), "static/fonts/OS600.woff")
        if len(caption) < 25:
            font = ImageFont.truetype(font_path, 25)
        elif len(caption) < 50:
            font = ImageFont.truetype(font_path, 15)
        else:
            font = ImageFont.truetype(font_path, 10)
        caption_width = font.getlength(caption)
        draw.text(
            ((img_width - caption_width) / 2, img_height - 40),
            text=caption,
            font=font,
            fill="black",
        )

    file_object = io.BytesIO()
    img.save(file_object, "PNG")
    img.close()

    return file_object


def convert_bytes_buffer_to_bytes_string(bytes_buffer: io.BytesIO) -> str:
    return base64.b64encode(bytes_buffer.getvalue()).decode('utf-8')


def generate_qr_codes_as_byte_strings(url_dict: Dict[str, str]) -> List[str]:
    """
    Takes a dict of the form {name:url} and returns a list of generated QR codes as
    byte strings
    """
    qr_code_byte_strings = []
    for caption, url in url_dict.items():
        qr_code_byte_buffer = generate_qr_code(url=url, caption=caption)
        qr_code_byte_strings.append(
            convert_bytes_buffer_to_bytes_string(bytes_buffer=qr_code_byte_buffer)
        )
    return qr_code_byte_strings
