"""Models for uploaded image information"""
import os
from os.path import exists, join
from django.db import models
from nav.models.profiles import Account
from nav.models.manage import Room
from nav.models.fields import VarcharField
from nav.path import localstatedir

ROOTPATH = join(localstatedir, 'uploads', 'images')


class Image(models.Model):
    """Model representing an uploaded image"""
    id = models.AutoField(db_column='imageid', primary_key=True)
    room = models.ForeignKey(Room, db_column='roomid')
    title = VarcharField()
    path = VarcharField()
    name = VarcharField()
    created = models.DateTimeField(auto_now_add=True)
    uploader = models.ForeignKey(Account, db_column='uploader')
    priority = models.IntegerField()

    class Meta(object):
        db_table = 'image'
        ordering = ['priority']

    def _check_image_existance(self):
        return exists(self.fullpath)

    def _check_thumb_existance(self):
        """Relies on static thumb directory"""
        return exists(self.thumbpath)

    def _check_readable(self):
        return os.access(self.fullpath, os.R_OK)

    def _get_url(self):
        return '/uploads/images/rooms/{path}/{name}'.format(
            path=self.path,
            name=self.name)

    def _get_thumb_url(self):
        return '/uploads/images/rooms/{path}/thumbs/{name}'.format(
            path=self.path,
            name=self.name)

    def _get_basepath(self):
        directory = 'rooms'
        return join(ROOTPATH, directory)

    def _get_fullpath(self):
        return join(self.basepath, self.path, self.name)

    def _get_thumb_path(self):
        return join(self.basepath, self.path, 'thumbs', self.name)

    image_exists = property(_check_image_existance)
    thumb_exists = property(_check_thumb_existance)
    is_readable = property(_check_readable)
    url = property(_get_url)
    thumb_url = property(_get_thumb_url)
    basepath = property(_get_basepath)
    fullpath = property(_get_fullpath)
    thumbpath = property(_get_thumb_path)
