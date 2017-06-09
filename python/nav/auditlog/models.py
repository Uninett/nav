# coding: UTF-8

# Copyright (C) 2017 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals, absolute_import

import json

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.encoding import force_text
from django.utils.timezone import now as utcnow

from nav.models.fields import VarcharField, LegacyGenericForeignKey

from . import find_modelname


@python_2_unicode_compatible
class LogEntry(models.Model):
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
    def add_log_entry(cls, actor, verb, template, subsystem=None, object=None, target=None, before=None, after=None):
        """LogEntry factory"""
        self = cls()
        dict = {'actor': actor, 'object': object, 'target': target}
        for k, v in dict.items():
            dict[k] = getattr(v, 'audit_logname', u'%s' % v)
        self.summary = template.format(**dict)
        self.verb = verb
        self.actor_model = find_modelname(actor)
        self.object_model = find_modelname(object) if object else None
        self.target_model = find_modelname(target) if target else None
        self.actor_pk = actor.pk
        self.object_pk = object.pk if object else None
        self.target_pk = target.pk if target else None
        self.timestamp = utcnow()
        self.subsystem = subsystem if subsystem else None
        self.before = force_text(before)
        self.after = force_text(after)
        self.save()
        return self

    def __str__(self):
        return self.summary
