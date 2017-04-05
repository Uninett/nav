# coding: UTF-8

from __future__ import unicode_literals

import json

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now as utcnow

from nav.models.fields import VarcharField, LegacyGenericForeignKey

from auditlog import find_modelname


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

    data_before = models.TextField(blank=True, null=True)
    data_after = models.TextField(blank=True, null=True)

    @classmethod
    def add_log_entry(cls, actor, verb, template, object=None, target=None, before=None, after=None):
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
        self.save()

    def __str__(self):
        return self.summary
