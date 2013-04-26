"""Models for room meta information"""
import os
from os.path import exists, join
from django.db import models
from nav.models.profiles import Account
from nav.models.manage import Room
from nav.models.fields import VarcharField
from nav.path import localstatedir

ROOMIMAGEPATH = join(localstatedir, 'uploads', 'images', 'rooms')


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

    class Meta:
        db_table = 'image'
        ordering = ['priority']

    def _check_image_existance(self):
        return exists(join(ROOMIMAGEPATH, self.path, self.name))

    def _check_thumb_existance(self):
        """Relies on static thumb directory"""
        return exists(join(ROOMIMAGEPATH, self.path, 'thumbs', self.name))

    def _check_readable(self):
        return os.access(join(ROOMIMAGEPATH, self.path, self.name), os.R_OK)

    image_exists = property(_check_image_existance)
    thumb_exists = property(_check_thumb_existance)
    is_readable = property(_check_readable)

