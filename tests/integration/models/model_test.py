"""
Query DB using Django models test

Intended purpose is to catch obvious omissions in DB state or the Django models
themselves.
"""

import os

from django.db import connection

import django.apps

get_models = django.apps.apps.get_models
del django.apps


import pytest

import nav.models

# Ensure that all modules are loaded
for file_name in os.listdir(os.path.dirname(nav.models.__file__)):
    if file_name.endswith('.py') and not file_name.startswith('__init__'):
        module_name = file_name.removesuffix('.py')
        __import__('nav.models.%s' % module_name)


@pytest.mark.parametrize("model", get_models())
def test_django_model(model):
    connection.close()  # Ensure clean connection
    list(model.objects.all()[:5])
