"""Generates syntax tests for all NAV Django templates"""

import os
from os.path import join, relpath
from django.conf import settings
from django.template import loader

from nav.eventengine.alerts import ensure_alert_templates_are_available
import pytest


def test_templates_can_be_found():
    ensure_alert_templates_are_available()
    templates = list(get_template_list())
    assert templates, "Can't find any Django templates"


def get_template_list():
    for tmpldir in settings.TEMPLATE_DIRS:
        for dirname, _subdirs, files in os.walk(tmpldir):
            for name in files:
                fullpath = join(dirname, name)
                yield relpath(fullpath, tmpldir)


@pytest.mark.parametrize("template_name", get_template_list())
def test_template_syntax(template_name):
    loader.get_template(template_name)
