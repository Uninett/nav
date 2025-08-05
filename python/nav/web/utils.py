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
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta
from typing import Literal

from django import forms
from django.http import FileResponse, HttpRequest, HttpResponse
from django.views.generic.list import ListView

import qrcode
import qrcode.image.svg
from PIL import ImageDraw, ImageFont


def is_ajax(request: HttpRequest) -> bool:
    """Returns True if this request is an AJAX (XMLHttpRequest) request"""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


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


def generate_png_qr_code(url: str, caption: str = "") -> bytes:
    """
    Generate a QR code from a given url, and, if given, adds a caption to it

    Returns the generated png image as bytes
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

    return file_object.getvalue()


def generate_svg_qr_code(url: str, caption: str = "") -> bytes:
    """
    Generate a QR code from a given url, and, if given, adds a caption to it

    Returns the generated svg image as bytes
    """
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)

    root = ET.fromstring(img.to_string(encoding="unicode"))
    if caption:
        if len(caption) < 25:
            font_size = "3"
        elif len(caption) < 50:
            font_size = "1.5"
        else:
            font_size = "1"
        text = ET.SubElement(
            root,
            "text",
            {
                "x": "50%",
                "y": "96%",
                "text-anchor": "middle",
                "font-size": font_size,
            },
        )
        text.text = caption

    del root.attrib["height"]
    del root.attrib["width"]

    ET.register_namespace("", "http://www.w3.org/2000/svg")

    return ET.tostring(root)


def generate_qr_code_as_string(
    url: str, caption: str = "", file_format: Literal["png", "svg"] = "png"
) -> str:
    """
    Takes an url, a caption (optional) and which file format the QR code should be and
    returns a QR code as string
    """
    qr_code_bytes = b""
    if file_format == "png":
        qr_code_bytes = generate_png_qr_code(url=url, caption=caption)
    elif file_format == "svg":
        qr_code_bytes = generate_svg_qr_code(url=url, caption=caption)

    return base64.b64encode(qr_code_bytes).decode('utf-8')


def generate_qr_codes_as_zip_response(
    url_dict: dict[str, str], file_format: Literal["png", "svg"] = "png"
) -> FileResponse:
    """
    Takes a dict of the form {name:url} and returns a FileResponse object that
    represents a ZIP file consisting of named PNG images of QR codes which map
    each name of the element to its url

    Returning the FileResponse in a Django view causes the ZIP file to be delivered
    in the form of a download attachment in web browsers
    """
    qr_codes_dict = dict()
    for caption, url in url_dict.items():
        if file_format == "png":
            qr_codes_dict[caption] = generate_png_qr_code(url=url, caption=caption)
        elif file_format == "svg":
            qr_codes_dict[caption] = generate_svg_qr_code(url=url, caption=caption)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for image_name, qr_code_bytes in qr_codes_dict.items():
            zf.writestr(image_name + "." + file_format, qr_code_bytes)
    buf.seek(0)

    return FileResponse(buf, as_attachment=True, filename="nav_qr_codes.zip")


def validate_timedelta_for_overflow(days: int = 0, hours: int = 0):
    """
    Validates that the given numbers of days and hours when subtracted from the
    current time will not result in an overflow error


    If that happens this function will raise a forms.ValidationError
    """
    try:
        datetime.now() - timedelta(days=days, hours=hours)
    except OverflowError:
        raise forms.ValidationError("They did not have computers that long ago")
