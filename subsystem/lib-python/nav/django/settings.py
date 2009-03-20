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

"""Django configuration wrapper around the NAV configuration files"""

from nav.config import readConfig
import nav.buildconf
import nav.path

nav_config = readConfig('nav.conf')
db_config = readConfig('db.conf')

DEBUG = nav_config.get('DJANGO_DEBUG', False)
TEMPLATE_DEBUG = DEBUG

# Admins
ADMINS = (
    ('NAV Administrator', nav_config['ADMIN_MAIL']),
)
MANAGERS = ADMINS

# Database / ORM configuration
DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = db_config['db_nav']
DATABASE_USER = db_config['script_django']
DATABASE_PASSWORD = db_config['userpw_%s' % DATABASE_USER]
DATABASE_HOST = db_config['dbhost']
DATABASE_PORT = db_config['dbport']

INSTALLED_APPS = ('nav.django',)

# URLs configuration
ROOT_URLCONF = 'nav.django.urls'

# Templates
TEMPLATE_DIRS = (
    nav.path.djangotmpldir,
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'nav.django.context_processors.debug',
    'nav.django.context_processors.account_processor',
)

# Email sending
DEFAULT_FROM_EMAIL = nav_config.get('DEFAULT_FROM_EMAIL', 'nav@localhost')

# Date formatting
DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'H:i:s'
DATETIME_FORMAT = '%s %s' % (DATE_FORMAT, TIME_FORMAT)

TIME_ZONE = nav_config.get('TIME_ZONE', 'Europe/Oslo')
DOMAIN_SUFFIX = nav_config.get('DOMAIN_SUFFIX', None)

# Cache backend. Used only for report subsystem in NAV 3.5.
# FIXME: Make this configurable in nav.conf (or possibly webfront.conf)
CACHE_BACKEND = 'file:///tmp/nav_cache?timeout=60'	
