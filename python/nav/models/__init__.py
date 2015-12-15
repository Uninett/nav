# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 UNINETT AS
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
"""Django ORM wrapper for the NAV manage database"""

import os
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

    import django
    django.setup()


# An overview of current preferences.
# They should start with PREFERENCE_KEY
PREFERENCE_KEY_LANGUAGE = 'language'  # AlertProfiles
PREFERENCE_KEY_STATUS = 'status-preferences'
PREFERENCE_KEY_WIDGET_COLUMNS = 'widget_columns'
PREFERENCE_KEY_REPORT_PAGE_SIZE = 'report_page_size'
