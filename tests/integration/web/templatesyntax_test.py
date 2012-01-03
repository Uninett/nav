#!/usr/bin/env python
"""Generates syntax tests for all NAV Django templates"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'
from os.path import sep, commonprefix, abspath, pardir, curdir, join

from django.conf import settings
from django.template import loader

def test_template_syntax():
    templates = get_template_list()
    for template in templates:
        testname = "does %s validate" % template
        yield testname, loader.get_template, template

def get_template_list():
    for tmpldir in settings.TEMPLATE_DIRS:
        for dirname, _subdirs, files in os.walk(tmpldir):
            for name in files:
                fullpath = join(dirname, name)
                yield relpath(fullpath, tmpldir)

def relpath(path, start=curdir):
    """Return a relative version of a path.

    Borrowed from python 2.6 stdlib for compatibility with python 2.5

    """
    if not path:
        raise ValueError("no path specified")

    start_list = abspath(start).split(sep)
    path_list = abspath(path).split(sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(commonprefix([start_list, path_list]))

    rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return curdir
    return join(*rel_list)
