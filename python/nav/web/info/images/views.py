import errno
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
            return HttpResponse(status=404)
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
            # Already gone; deletion is idempotent, treat as success
            messages.info(request, 'Image was already deleted')
            return HttpResponse(status=200)
        else:
            filepath = image.fullpath
            try:
                _logger.debug('Deleting file %s', filepath)
                os.unlink(filepath)
            except OSError as error:
                # A missing file is fine; any other error is a real problem
                if error.errno != errno.ENOENT:
                    _logger.error('Could not delete image file %s: %s', filepath, error)
                    return HttpResponse(status=500)

            try:
                os.unlink(image.thumbpath)
            except OSError:
                # We don't really care if the thumbnail is not deleted
                pass

            # Fetch all image instances that uses this image and delete them
            Image.objects.filter(path=image.path, name=image.name).delete()
            messages.success(request, 'Image &laquo;%s&raquo; deleted' % image.title)

    return HttpResponse(status=200)


def update_priority(request):
    """Update the order of image objects"""
    if request.method == 'POST':
        for key, value in request.POST.items():
            _logger.debug('%s=%s', key, value)
            try:
                image = Image.objects.get(pk=key)
            except Image.DoesNotExist:
                return HttpResponse(status=404)
            image.priority = value
            image.save()

    return HttpResponse(status=200)
