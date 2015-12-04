import os
from django import setup


def pytest_configure():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'
    setup()
