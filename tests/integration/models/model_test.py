# Copyright (C) 2010 UNINETT AS
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

import os

import nav.models

from django.db import connection
from django.db.models import get_models


'''
Query DB using Django models test

Intended purpose is to catch obvious omissions in DB state or the Django models
themselves.
'''

# Ensure that all modules are loaded
for file_name in os.listdir(os.path.dirname(nav.models.__file__)):
    if file_name.endswith('.py') and not file_name.startswith('__init__'):
        module_name = file_name.replace('.py', '')
        __import__('nav.models.%s' % module_name)

def check_model(model):
    connection.close() # Ensure clean connection
    list(model.objects.all()[:5])

def test_models():
    for model in get_models():
        model_name = "%s.%s" % (model.__module__,
                                model.__name__)
        yield "%s seems up to date" % model_name, check_model, model
