#
# Copyright (C) 2007-2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Django ORM wrapper for the NAV logger database
"""

from django.db import models

from nav.models.fields import VarcharField


class LoggerCategory(models.Model):
    """
    Model for the logger.category-table
    """

    category = VarcharField(db_column='category', unique=True, primary_key=True)

    def __str__(self):
        return self.category

    class Meta(object):
        db_table = '"logger"."category"'


class Origin(models.Model):
    """
    Model for the logger.origin-table
    """

    origin = models.AutoField(db_column='origin', primary_key=True)
    name = VarcharField(db_column='name')
    category = models.ForeignKey(
        LoggerCategory,
        on_delete=models.CASCADE,
        db_column='category',
        related_name="origins",
    )

    def __str__(self):
        return self.name

    class Meta(object):
        db_table = '"logger"."origin"'


class Priority(models.Model):
    """
    Model for the logger.priority-table
    """

    priority = models.AutoField(db_column='priority', primary_key=True)
    keyword = VarcharField(db_column='keyword', unique=True)
    description = VarcharField(db_column='description')

    def __str__(self):
        return self.keyword

    class Meta(object):
        db_table = '"logger"."priority"'


class LogMessageType(models.Model):
    """
    Model for the logger.log_message_type-table
    """

    type = models.AutoField(db_column='type', primary_key=True)
    priority = models.ForeignKey(
        Priority,
        on_delete=models.CASCADE,
        db_column='priority',
        related_name="log_message_types",
    )
    facility = VarcharField(db_column='facility')
    mnemonic = VarcharField(db_column='mnemonic')

    def __str__(self):
        return "{0}-{1}-{2}".format(self.facility, self.priority, self.mnemonic).upper()

    class Meta(object):
        db_table = '"logger"."log_message_type"'
        unique_together = (('priority', 'facility', 'mnemonic'),)


class LogMessage(models.Model):
    """
    Model for the logger.log_message-table
    """

    id = models.AutoField(db_column='id', primary_key=True)
    time = models.DateTimeField(db_column='time', auto_now=True)
    origin = models.ForeignKey(
        Origin,
        on_delete=models.CASCADE,
        db_column='origin',
        related_name="log_messages",
    )
    newpriority = models.ForeignKey(
        Priority,
        on_delete=models.CASCADE,
        db_column='newpriority',
        related_name="log_messages",
    )
    type = models.ForeignKey(
        LogMessageType,
        on_delete=models.CASCADE,
        db_column='type',
        related_name="log_messages",
    )
    message = VarcharField(db_column='message')

    class Meta(object):
        db_table = '"logger"."log_message"'


class ErrorError(models.Model):
    """
    Model for the logger.errorerror-table
    """

    id = models.AutoField(db_column='id', primary_key=True)
    message = VarcharField(db_column='message')

    class Meta(object):
        db_table = '"logger"."errorerror"'


class MessageView(models.Model):
    """
    This is actually a class for a database-view 'message_view'.

    Do not change attributes unless You know what You are doing!
    Check: https://docs.djangoproject.com/en/dev/ref/models/options/
    """

    origin = models.ForeignKey(
        Origin,
        on_delete=models.CASCADE,
        db_column='origin',
        primary_key=True,
        related_name="message_views",
    )
    type = models.ForeignKey(
        LogMessageType,
        on_delete=models.CASCADE,
        db_column='type',
        related_name="message_views",
    )
    newpriority = models.ForeignKey(
        Priority,
        on_delete=models.CASCADE,
        db_column='newpriority',
        related_name="message_views",
    )
    category = models.ForeignKey(
        LoggerCategory,
        on_delete=models.CASCADE,
        db_column='category',
        related_name="message_views",
    )
    time = models.DateTimeField(db_column='time')

    class Meta(object):
        db_table = '"logger"."message_view"'
        # Models for database-views must set this option.
        managed = False
