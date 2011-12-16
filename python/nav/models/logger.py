# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
"""

from django.db import models
from nav.models.fields import VarcharField

class Category(models.Model):
    id = models.AutoField(db_column='category_id', primary_key=True)
    category = VarcharField(db_column='category', unique=True)

    class Meta:
        db_table = 'category'

class Origin(models.Model):
    origin = models.AutoField(db_column='origin', primary_key=True)
    name = VarcharField(db_column='name')
    category = models.ForeignKey(Category, db_column='category')

    class Meta:
        db_table = 'origin'

class Priority(models.Model):
    priority = models.AutoField(db_column='priority', primary_key=True)
    keyword = VarcharField(db_column='keyword', unique=True)
    description = VarcharField(db_column='description')

    class Meta:
        db_table = 'priority'

class LogMessageType(models.Model):
    type = models.AutoField(db_column='type', primary_key=True)
    priority = models.ForeignKey(Priority, db_column='priority')
    facility = VarcharField(db_column='facility')
    mnemonic = VarcharField(db_column='mnemonic')

    class Meta:
        db_table = 'log_message_type'
        unique_together = (('priority', 'facility', 'mnemonic'),)

class LogMessage(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    time = models.DateTimeField(db_column='time', auto_now=True)
    origin = models.ForeignKey(Origin, db_column='origin')
    newpriority = models.ForeignKey(Priority, db_column='newpriority')
    type = models.ForeignKey(LogMessageType, db_column='type')
    message = VarcharField(db_column='message')

    class Meta:
        db_table = 'log_message'

class ErrorError(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    message = VarcharField(db_column='message')

    class Meta:
        db_table = 'errorerror'

class MessageView(models.Model):
    """
    This is actually a class for a database-view 'message_view'.

    Do not change attributes unless You know what You are doing!
    Check: https://docs.djangoproject.com/en/dev/ref/models/options/
    """
    origin = models.IntegerField(db_column='origin', primary_key=True)
    type = models.IntegerField(db_column='type')
    newpriority = models.IntegerField(db_column='newpriority')
    category = models.IntegerField(db_column='category')
    time =  models.DateTimeField(db_column='time')

    class Meta:
        db_table = 'message_view'
        # Models for database-views must set this option.
        managed = False
