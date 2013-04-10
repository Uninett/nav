"""Models for room meta information"""
from django.db import models
from nav.models.profiles import Account
from nav.models.manage import Room

from nav.models.fields import VarcharField


class Image(models.Model):
    """Model representing an uploaded image"""
    id = models.AutoField(db_column='imageid', primary_key=True)
    room = models.ForeignKey(Room, db_column='roomid')
    title = VarcharField()
    path = VarcharField()
    name = VarcharField()
    created = models.DateTimeField(auto_now_add=True)
    uploader = models.ForeignKey(Account, db_column='uploader')

    class Meta:
        db_table = 'image'
