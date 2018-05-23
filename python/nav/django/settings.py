#
# Copyright (C) 2007-2015 Uninett AS
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

import os
import sys
import copy

from django.utils.log import DEFAULT_LOGGING

from nav.config import read_flat_config, getconfig
from nav.db import get_connection_parameters
import nav.buildconf

ALLOWED_HOSTS = ['*']

try:
    nav_config = read_flat_config('nav.conf')
except IOError:
    nav_config = {'SECRET_KEY': 'Very bad default value'}

try:
    webfront_config = getconfig('webfront/webfront.conf',
                                configfolder=nav.buildconf.sysconfdir)
except IOError:
    webfront_config = {}

DEBUG = nav_config.get('DJANGO_DEBUG', 'False').upper() in ('TRUE', 'YES', 'ON')

# Copy Django's default logging config, but modify it to enable HTML e-mail
# part for improved debugging:
LOGGING = copy.deepcopy(DEFAULT_LOGGING)
_handlers = LOGGING.get('handlers', {})
_mail_admin_handler = _handlers.get('mail_admins', {})
_mail_admin_handler['include_html'] = True

# Admins
ADMINS = (
    ('NAV Administrator', nav_config.get('ADMIN_MAIL', 'root@localhost')),
)
MANAGERS = ADMINS

# Database / ORM configuration
try:
    _appname = os.path.basename(sys.argv[0])
    _host, _port, _name, _user, _password = get_connection_parameters('django')
    DATABASES = {
        'default': {
            'NAME': _name,
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': _host,
            'PORT': _port,
            'USER': _user,
            'PASSWORD': _password,
            'CONN_MAX_AGE': 300,  # 5 minutes
            'OPTIONS': {
                'application_name': _appname or 'NAV',
            }

        }
    }
except IOError:
    pass

# URLs configuration
ROOT_URLCONF = 'nav.django.urls'

#Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(nav.buildconf.webrootdir, 'static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


# Templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(nav.buildconf.sysconfdir, 'templates'),
            nav.buildconf.djangotmpldir,
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.core.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'nav.django.context_processors.debug',
                'nav.django.context_processors.account_processor',
                'nav.django.context_processors.nav_version',
                'nav.django.context_processors.graphite_base',
                'nav.django.context_processors.footer_info',
                'django.core.context_processors.static',
            ],
            'debug': DEBUG,
        },
    }
]

TEMPLATE_DEBUG = DEBUG                       # XXX Pre Django 1.8
TEMPLATE_DIRS = tuple(TEMPLATES[0]['DIRS'])  # XXX Pre Django 1.8
TEMPLATE_CONTEXT_PROCESSORS = tuple(         # XXX Pre Django 1.8
    TEMPLATES[0]['OPTIONS']['context_processors']
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

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = int(
    webfront_config.get('sessions', {}).get('timeout', 3600))
SESSION_COOKIE_NAME = 'nav_sessionid'
SESSION_SAVE_EVERY_REQUEST = True

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
SHORT_TIME_FORMAT = 'H:i'  # Use template filter to access this
DATETIME_FORMAT = '%s %s' % (DATE_FORMAT, TIME_FORMAT)
SHORT_DATETIME_FORMAT = '%s %s' % (DATE_FORMAT, SHORT_TIME_FORMAT)

TIME_ZONE = nav_config.get('TIME_ZONE', 'Europe/Oslo')
DOMAIN_SUFFIX = nav_config.get('DOMAIN_SUFFIX', None)

# Cache backend. Used only for report subsystem in NAV 3.5.
# FIXME: Make this configurable in nav.conf (or possibly webfront.conf)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/nav_cache',
        'TIMEOUT': '60'
    }
}


SECRET_KEY = nav_config.get('SECRET_KEY', None) # Must be set in nav.conf!

# Because registering hstore extension in a database may lead to problems
# with type conversion, force registering of hstore on each new connection
# See https://github.com/djangonauts/django-hstore/pull/35
DJANGO_HSTORE_GLOBAL_REGISTER = False

NAVLETS = (
    'nav.web.navlets.machinetracker.MachineTrackerNavlet',
    'nav.web.navlets.error.ErrorWidget',
    'nav.web.navlets.vlangraph.VlanGraphNavlet',
    'nav.web.navlets.portadmin.PortadminNavlet',
    'nav.web.navlets.linklist.LinkListNavlet',
    'nav.web.navlets.messages.MessagesNavlet',
    'nav.web.navlets.welcome.WelcomeNavlet',
    'nav.web.navlets.room_map.RoomMapNavlet',
    'nav.web.navlets.feedreader.FeedReaderNavlet',
    'nav.web.navlets.navblog.NavBlogNavlet',
    'nav.web.navlets.gettingstarted.GettingStartedWidget',
    'nav.web.navlets.graph.GraphWidget',
    'nav.web.navlets.watchdog.WatchDogWidget',
    'nav.web.navlets.status2.Status2Widget',
    'nav.web.navlets.report.ReportWidget',
    'nav.web.navlets.sensor.SensorWidget',
    'nav.web.navlets.alert.AlertWidget',
    'nav.web.navlets.ups.UpsWidget',
    'nav.web.navlets.pdu.PduWidget',
    'nav.web.navlets.roomstatus.RoomStatus',
    'nav.web.navlets.locationstatus.LocationStatus',
    'nav.web.navlets.env_rack.EnvironmentRackWidget',
)

CRISPY_TEMPLATE_PACK = 'foundation'

INSTALLED_APPS = (
    'nav.models',
    'nav.django',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_forms_foundation',
    'django_hstore',
    'rest_framework',
    'nav.auditlog',
)

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'PAGINATE_BY': 100,
    'PAGINATE_BY_PARAM': 'page_size',
}

# Classes that implement a search engine for the web navbar
SEARCHPROVIDERS = [
    'nav.web.info.searchproviders.RoomSearchProvider',
    'nav.web.info.searchproviders.LocationSearchProvider',
    'nav.web.info.searchproviders.NetboxSearchProvider',
    'nav.web.info.searchproviders.InterfaceSearchProvider',
    'nav.web.info.searchproviders.VlanSearchProvider',
    'nav.web.info.searchproviders.PrefixSearchProvider',
    'nav.web.info.searchproviders.DevicegroupSearchProvider',
    'nav.web.info.searchproviders.UnrecognizedNeighborSearchProvider',
]

# Hack for hackers to use features like debug_toolbar etc.
# https://code.djangoproject.com/wiki/SplitSettings (Rob Golding's method)
sys.path.append(os.path.join(nav.buildconf.sysconfdir, "python"))
try:
    # pylint: disable=E0602
    LOCAL_SETTINGS
except NameError:
    try:
        # pylint: disable=F0401
        from local_settings import *
    except ImportError:
        pass
