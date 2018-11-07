#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
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

from nav.bootstrap import bootstrap_django
bootstrap_django(__file__)

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
