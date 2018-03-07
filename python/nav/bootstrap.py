from __future__ import absolute_import, print_function

from os.path import dirname, realpath
import os
import sys

import django
from django.apps import apps
from django.utils.timezone import now


__all__ = ['bootstrap_django']

RUN = False


def bootstrap_django(caller=None):
    global RUN

    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

    mydir = dirname(dirname(realpath(__file__)))
    sys.path.append(mydir)
    with open('/tmp/bootstrap_django.log', 'a') as F:
        F.write('{}\n'.format(now()))
        if caller:
            F.write('{}\n'.format(caller))
        F.write('\n')

    if not RUN and not apps.ready:
        django.setup()
        RUN = True
