#!/usr/bin/env python
"""Generates syntax tests for all NAV Django templates"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'
from os.path import sep, commonprefix, abspath, pardir, curdir, join, relpath

from django.conf import settings
from django.template import loader

from nav.eventengine.alerts import ensure_alert_templates_are_available

def test_template_syntax():
    ensure_alert_templates_are_available()
    templates = list(get_template_list())
    assert templates, "Can't find any Django templates"
    for template in templates:
        testname = "does %s validate" % template
        yield testname, loader.get_template, template

def get_template_list():
    for tmpldir in settings.TEMPLATE_DIRS:
        for dirname, _subdirs, files in os.walk(tmpldir):
            for name in files:
                fullpath = join(dirname, name)
                yield relpath(fullpath, tmpldir)
