# coding: utf-8

# Copyright (C) 2017 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.


import logging
from django.utils.encoding import force_str

from django.db import models
from django.utils.timezone import now as utcnow

from nav.models.fields import VarcharField, LegacyGenericForeignKey

from . import find_modelname

_logger = logging.getLogger(__name__)


class LogEntry(models.Model):
    """
    Logs mostly user actions in NAV

    Example logentry:
    LogEntry.add_log_entry(
        account,           # actor
        u'set-ifalias',    # verb
        u'{actor}: {object} - ifalias set to "%s"' % ifalias,  # template
        subsystem=u'portadmin',                                # optional
        object=interface,                                      # optional
    )
    """

    actor_model = VarcharField()
    actor_pk = VarcharField()
    actor = LegacyGenericForeignKey('actor_model', 'actor_pk')

    object_model = VarcharField(null=True)
    object_pk = VarcharField(null=True)
    object = LegacyGenericForeignKey('object_model', 'object_pk')

    target_model = VarcharField(null=True)
    target_pk = VarcharField(null=True)
    target = LegacyGenericForeignKey('target_model', 'target_pk')

    timestamp = models.DateTimeField()

    verb = models.SlugField()

    summary = models.TextField()

    subsystem = VarcharField(blank=True, null=True)

    before = models.TextField(blank=True, null=True)
    after = models.TextField(blank=True, null=True)

    @classmethod
    def add_log_entry(
        cls,
        actor,
        verb,
        template,
        subsystem=None,
        object=None,
        target=None,
        before=None,
        after=None,
    ):
        """LogEntry factory"""
        self = cls()
        dict = {'actor': actor, 'object': object, 'target': target}
        for k, v in dict.items():
            dict[k] = getattr(v, 'audit_logname', '%s' % v)
        try:
            self.summary = template.format(**dict)
        except KeyError as error:
            self.summary = 'Error creating summary - see error log'
            _logger.error('KeyError when creating summary: %s', error)
        self.verb = verb
        self.actor_model = find_modelname(actor)
        self.object_model = find_modelname(object) if object else None
        self.target_model = find_modelname(target) if target else None
        self.actor_pk = actor.pk
        self.object_pk = object.pk if object else None
        self.target_pk = target.pk if target else None
        self.timestamp = utcnow()
        self.subsystem = subsystem if subsystem else None
        self.before = force_str(before)
        self.after = force_str(after)
        self.save()
        return self

    @staticmethod
    def add_create_entry(actor, obj):
        """Add log entry for created objects

        :type actor: nav.models.profiles.Account
        """
        model = obj.__class__.__name__.lower()
        LogEntry.add_log_entry(
            actor,
            'create-{}'.format(model),
            '{actor} created {object}',
            after=obj,
            object=obj,
        )

    @staticmethod
    def add_delete_entry(actor, obj, template=None):
        """Add log entry for deleted objects"""
        model = obj.__class__.__name__.lower()
        template = template or '{actor} deleted {object}'
        LogEntry.add_log_entry(
            actor, 'delete-{}'.format(model), template, before=obj, object=obj
        )

    @staticmethod
    def add_edit_entry(actor, old, new, attribute, include_values=True):
        """Add log entry for edited objects

        :type attribute: str
        """

        def dict_to_string(d):
            """
            {"a": "b", "c": "d"} => "a=b, c=d"
            """
            return ", ".join("{}={}".format(x, y) for x, y in d.items())

        model = new.__class__.__name__.lower()
        prefix = '{actor} edited {object}'
        old_value = getattr(old, attribute)
        new_value = getattr(new, attribute)
        if include_values:
            # Dicts fucks up the template, try to intervene
            if isinstance(old_value, dict):
                old_value = dict_to_string(old_value)
            if isinstance(new_value, dict):
                new_value = dict_to_string(new_value)
            summary = "{} changed from '{}' to '{}'".format(
                attribute, old_value, new_value
            )
        else:
            summary = "{} changed".format(attribute)

        LogEntry.add_log_entry(
            actor,
            'edit-{}-{}'.format(model, attribute),
            '{}: {}'.format(prefix, summary),
            before=old,
            after=new,
            object=new,
        )

    @staticmethod
    def compare_objects(actor, old, new, attribute_list, censored_attributes=None):
        """Checks for differences in two objects given an attribute-list

        :type actor: nav.models.profiles.Account
        :type old: models.Model
        :type new: models.Model
        :type attribute_list: list[str]

        Adds a log entry for each attribute where the two objects differ.
        """
        if censored_attributes is None:
            censored_attributes = []

        for attribute in attribute_list:
            old_value = getattr(old, attribute)
            new_value = getattr(new, attribute)
            if old_value != new_value:
                include_values = attribute not in censored_attributes
                LogEntry.add_edit_entry(
                    actor, old, new, attribute, include_values=include_values
                )

    def __str__(self):
        return self.summary
