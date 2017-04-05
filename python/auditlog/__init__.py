# coding: UTF-8

from __future__ import unicode_literals


default_app_config = 'auditlog.apps.AuditlogConfig'

def find_modelname(obj):
    try:
        # Django <= 1.7.*
        return obj._meta.db_table
    except AttributeError:
        return obj
