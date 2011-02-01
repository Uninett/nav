# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Main Django URL configuration"""

# pylint: disable=W0614,W0401

# Import all submodules in the urls package
import os
__all__ = []
for file_name in os.listdir(os.path.dirname(__file__)):
    if file_name.endswith('.py') and not file_name.startswith('__init__'):
        module_name = file_name.replace('.py', '')
        __all__.append(module_name)
from nav.django.urls import *

# Combine urlpatterns from all the submodules
from django.conf.urls.defaults import *
urlpatterns = patterns('')
for module_name in __all__:
    urlpatterns += eval(module_name + '.get_urlpatterns()')

