#
# Copyright (C) 2007-2011 UNINETT AS
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

from nav.config import read_flat_config, getconfig
from nav.db import get_connection_parameters
import nav.buildconf
import nav.path

try:
    nav_config = read_flat_config('nav.conf')
except IOError:
    nav_config = {}

try:
    webfront_config = getconfig('webfront/webfront.conf',
                                configfolder=nav.path.sysconfdir)
except IOError:
    webfront_config = {}

DEBUG = nav_config.get('DJANGO_DEBUG', False)
TEMPLATE_DEBUG = DEBUG

# Admins
ADMINS = (
    ('NAV Administrator', nav_config.get('ADMIN_MAIL', 'root@localhost')),
)
MANAGERS = ADMINS

# Database / ORM configuration
try:
    _host, _port, _name, _user, _password = get_connection_parameters('django')
    DATABASES = {
        'default': {
            'NAME': _name,
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': _host,
            'PORT': _port,
            'USER': _user,
            'PASSWORD': _password,
        }
    }
except IOError:
    pass

INSTALLED_APPS = ('nav.django', 'django.contrib.sessions')

# URLs configuration
ROOT_URLCONF = 'nav.django.urls'

# Templates
TEMPLATE_DIRS = (
    nav.path.djangotmpldir,
)

# Context processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'nav.django.context_processors.debug',
    'nav.django.context_processors.account_processor',
    'nav.django.context_processors.nav_version',
)

# Middleware
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'nav.django.auth.AuthenticationMiddleware',
    'nav.django.auth.AuthorizationMiddleware',
    'nav.django.legacy.LegacyCleanupMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = int(
    webfront_config.get('sessions', {}).get('timeout', 3600))

# Message storage for the messages framework
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Email sending
DEFAULT_FROM_EMAIL = nav_config.get('DEFAULT_FROM_EMAIL', 'nav@localhost')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_HOST = nav_config.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = nav_config.get('EMAIL_PORT', 25)

EMAIL_HOST_USER = nav_config.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = nav_config.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = nav_config.get('EMAIL_USE_TLS', 'False') == 'True'

# Date formatting
DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'H:i:s'
DATETIME_FORMAT = '%s %s' % (DATE_FORMAT, TIME_FORMAT)

TIME_ZONE = nav_config.get('TIME_ZONE', 'Europe/Oslo')
DOMAIN_SUFFIX = nav_config.get('DOMAIN_SUFFIX', None)

# Cache backend. Used only for report subsystem in NAV 3.5.
# FIXME: Make this configurable in nav.conf (or possibly webfront.conf)
CACHE_BACKEND = 'file:///tmp/nav_cache?timeout=60'	

NAVLETS = (
    'nav.web.navlets.machinetracker.MachineTrackerNavlet',
    'nav.web.navlets.status.StatusNavlet',
    'nav.web.navlets.vlangraph.VlanGraphNavlet',
)
