import logging
from os.path import join

from django.contrib import messages

from nav.django.utils import get_account
from nav.models.images import Image
from nav.web.info.images.utils import (get_extension, create_hash,
                                       create_image_directory,
                                       get_next_priority, save_image,
                                       save_thumbnail)

_logger = logging.getLogger('nav.web.info.image')


def handle_image_upload(request, **kwargs):
    account = get_account(request)
    images = request.FILES.getlist('images')
    for image in images:
        try:
            handle_image(image, uploader=account, **kwargs)
            messages.success(
                request, 'Image &laquo;%s&raquo; uploaded' % image.name)
        except IOError as e:
            _logger.error(e)
            messages.error(request, 'Image &laquo;%s&raquo; not saved - '
                                    'perhaps unsupported type' % image.name)


def handle_image(image, uploader, room=None):
    _logger.debug('Uploading image %s', image)
    original_name = image.name
    imagename = "%s%s" % (create_hash(image, True),
                          get_extension(original_name))
    imagedirectory = create_hash(room.id)
    image_obj = Image(title=original_name, path=imagedirectory, name=imagename,
                      room=room, priority=get_next_priority(room),
                      uploader=uploader)
    imagedirectorypath = join(image_obj.basepath, imagedirectory)
    create_image_directory(imagedirectorypath)
    save_image(image, join(imagedirectorypath, imagename))
    save_thumbnail(imagename, imagedirectorypath,
                   join(imagedirectorypath, 'thumbs'))
    image_obj.save()
