"""
Query DB using Django models test

Intended purpose is to catch obvious omissions in DB state or the Django models
themselves.
"""
import os

from django.db import connection

try:
    # Django >= 1.8
    import django.apps
    get_models = django.apps.apps.get_models
    del django.apps
except ImportError:
    # Django < 1.9
    from django.db.models import get_models

import pytest

import nav.models

# Ensure that all modules are loaded
for file_name in os.listdir(os.path.dirname(nav.models.__file__)):
    if file_name.endswith('.py') and not file_name.startswith('__init__'):
        module_name = file_name.replace('.py', '')
        __import__('nav.models.%s' % module_name)


@pytest.mark.parametrize("model", get_models())
def test_django_model(model):
    connection.close()  # Ensure clean connection
    list(model.objects.all()[:5])
