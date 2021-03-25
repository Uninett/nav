import logging
import os

from django.contrib import messages
from django.http import HttpResponse

from nav.models.images import Image

_logger = logging.getLogger('nav.web.info.image')


def update_title(request):
    """Update the title for a room image"""
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


def delete_image(request):
    """Delete an image from a room"""
    if request.method == 'POST':
        imageid = int(request.POST['id'])

        _logger.debug('Deleting image %s', imageid)

        try:
            image = Image.objects.get(pk=imageid)
        except Image.DoesNotExist:
            return HttpResponse(status=500)
        else:
            filepath = image.fullpath
            try:
                _logger.debug('Deleting file %s', filepath)
                os.unlink(filepath)
            except OSError as error:
                # If the file is not found, then this is ok, otherwise not ok
                if error.errno != 2:
                    return HttpResponse(status=500)
            else:
                messages.success(
                    request, 'Image &laquo;%s&raquo; deleted' % image.title
                )

            try:
                os.unlink(image.thumbpath)
            except OSError:
                # We don't really care if the thumbnail is not deleted
                pass

            # Fetch all image instances that uses this image and delete them
            Image.objects.filter(path=image.path, name=image.name).delete()

    return HttpResponse(status=200)


def update_priority(request):
    """Update the order of image objects"""
    if request.method == 'POST':
        for key, value in request.POST.items():
            _logger.debug('%s=%s', key, value)
            image = Image.objects.get(pk=key)
            image.priority = value
            image.save()

    return HttpResponse(status=200)
