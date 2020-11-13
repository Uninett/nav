#
# Copyright (C) 2007-2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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

import django
from django.utils.log import DEFAULT_LOGGING

from nav.config import (NAV_CONFIG, getconfig, find_config_dir)
from nav.db import get_connection_parameters
import nav.buildconf

ALLOWED_HOSTS = ['*']

_config_dir = find_config_dir()
try:
    _webfront_config = getconfig('webfront/webfront.conf')
except (IOError, OSError):
    _webfront_config = {}

DEBUG = NAV_CONFIG.get('DJANGO_DEBUG', 'False').upper() in ('TRUE', 'YES', 'ON')

# Copy Django's default logging config, but modify it to enable HTML e-mail
# part for improved debugging:
LOGGING = copy.deepcopy(DEFAULT_LOGGING)
_handlers = LOGGING.get('handlers', {})
_mail_admin_handler = _handlers.get('mail_admins', {})
_mail_admin_handler['include_html'] = True

# Admins
ADMINS = (
    ('NAV Administrator', NAV_CONFIG.get('ADMIN_MAIL', 'root@localhost')),
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
except (IOError, OSError):
    pass

# URLs configuration
ROOT_URLCONF = 'nav.django.urls'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(nav.buildconf.webrootdir, 'static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
# This is a custom NAV setting for upload directory location:
UPLOAD_DIR = NAV_CONFIG.get(
    'UPLOAD_DIR',
    os.path.join(nav.buildconf.localstatedir, 'uploads'))

STATICFILES_DIRS = [
    ('uploads', UPLOAD_DIR),
]
# Mount the NAV docs if running under the Django development server
_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
_doc_dir = os.path.join(_base_dir, 'build/sphinx/html')
if os.path.isdir(_doc_dir):
    STATICFILES_DIRS.append(('doc', _doc_dir))


# Templates
_global_template_dir = [
    os.path.join(_config_dir, 'templates')] if _config_dir else []

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': _global_template_dir + [nav.buildconf.djangotmpldir],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'nav.django.context_processors.debug',
                'nav.django.context_processors.account_processor',
                'nav.django.context_processors.nav_version',
                'nav.django.context_processors.graphite_base',
                'nav.django.context_processors.footer_info',
                'nav.django.context_processors.auth',
                'django.template.context_processors.static',
            ],
            'debug': DEBUG,
            "builtins": ["nav.django.templatetags.query"],
        },
    }
]

# Middleware
MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'nav.web.auth.AuthenticationMiddleware',
    'nav.web.auth.AuthorizationMiddleware',
    'nav.django.legacy.LegacyCleanupMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)
if django.VERSION[:2] == (1, 8):  # Django <= 1.8
    MIDDLEWARE_CLASSES = MIDDLEWARE

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = int(
    _webfront_config.get('sessions', {}).get('timeout', 3600)
)
SESSION_COOKIE_NAME = 'nav_sessionid'
SESSION_SAVE_EVERY_REQUEST = False

# Message storage for the messages framework
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Email sending
DEFAULT_FROM_EMAIL = NAV_CONFIG.get('DEFAULT_FROM_EMAIL', 'nav@localhost')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_HOST = NAV_CONFIG.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(NAV_CONFIG.get('EMAIL_PORT', 25))

EMAIL_HOST_USER = NAV_CONFIG.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = NAV_CONFIG.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = NAV_CONFIG.get('EMAIL_USE_TLS', 'False') == 'True'

# Date formatting
DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'H:i:s'
SHORT_TIME_FORMAT = 'H:i'  # Use template filter to access this
DATETIME_FORMAT = '%s %s' % (DATE_FORMAT, TIME_FORMAT)
SHORT_DATETIME_FORMAT = '%s %s' % (DATE_FORMAT, SHORT_TIME_FORMAT)

TIME_ZONE = NAV_CONFIG.get('TIME_ZONE', 'Europe/Oslo')
DOMAIN_SUFFIX = NAV_CONFIG.get('DOMAIN_SUFFIX', None)

# Cache backend. Used only for report subsystem in NAV 3.5.
# FIXME: Make this configurable in nav.conf (or possibly webfront.conf)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/nav_cache',
        'TIMEOUT': '60'
    }
}


SECRET_KEY = NAV_CONFIG.get('SECRET_KEY', 'Very bad default value!')

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

CRISPY_ALLOWED_TEMPLATE_PACKS = ('foundation-5')
CRISPY_TEMPLATE_PACK = 'foundation-5'

INSTALLED_APPS = (
    'nav.models',
    'nav.web',
    'nav.django',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.humanize',
    'django_filters',
    'crispy_forms',
    'crispy_forms_foundation',
    'rest_framework',
    'nav.auditlog',
    'nav.web.macwatch',
    'nav.web.geomap',
    'nav.portadmin.napalm',
    'nav.web.portadmin',
    'django.contrib.postgres',
)

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'nav.web.api.v1.NavPageNumberPagination',
    'UNAUTHENTICATED_USER': 'nav.django.utils.default_account',
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
if _config_dir:
    sys.path.append(os.path.join(_config_dir, "python"))
try:
    # pylint: disable=E0602
    LOCAL_SETTINGS
except NameError:
    try:
        # pylint: disable=F0401
        from local_settings import *
    except ImportError:
        pass
