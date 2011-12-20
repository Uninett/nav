# -*- coding: UTF-8 -*-
#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Utility-classes for logghandler.

Do database-operations and get hold of parameters in the URL.
"""

import logging
import re
import datetime

import nav
from nav.models.logger import LoggerCategory
from nav.models.logger import Origin
from nav.models.logger import Priority
from nav.models.logger import LogMessageType


class DbAccess(object):
    """
    A class that does all the fetching from the database, prepare
    values to be displayed in the web-pages and make helper-maps.
    """
    logger = logging.getLogger("nav.web.loggerhandler.utils.DbAccess")

    DOMAIN_SUFFICES = nav.config.readConfig(
                                    "nav.conf")["DOMAIN_SUFFIX"].split(",")
    DOMAIN_SUFFICES = [s.strip() for s in DOMAIN_SUFFICES]

    def __init__(self):
        super(DbAccess, self).__init__()
        self.db_categories = None
        self.db_priorities = None
        self.db_origins = None
        self.db_message_types = None

        self.categories = None
        self.priorities = None
        self.legal_priorities = None

        self.origins = None
        self.originid2origin = None
        self.origin2originid = None

        self.types = None
        self.typeid2type = None
        self.type2typeid = None

    def _get_categories_db(self):
        """
        Fetch and cache all category-rows from database.
        """
        if not self.db_categories:
            self.db_categories = LoggerCategory.objects.all()
        return self.db_categories

    def _get_priorities_db(self):
        """
        Fetch and cache all priority-rows from database.
        """
        if not self.db_priorities:
            self.db_priorities = Priority.objects.all()
        return self.db_priorities

    def _get_origins_db(self):
        """
        Fetch and cache all origin-rows from database.
        """
        if not self.db_origins:
            self.db_origins = Origin.objects.all()
        return self.db_origins

    def _get_message_types_db(self):
        """
        Fetch and cache all log_message_type-rows from database.
        """
        if not self.db_message_types:
            self.db_message_types = LogMessageType.objects.all()
        return self.db_message_types

    def get_categories(self):
        """
        Prepare all categories for display in web-page.
        """
        if not self.categories:
            self.categories = []
            self.categories.append(('(All)'))
            for cat in self._get_categories_db():
                self.categories.append((cat.cat_name))
        return self.categories

    def get_priorities(self):
        """
        Prepare all priorities for display in web-page.
        """
        if not self.priorities:
            self.priorities = []
            self.priorities.append(("-", "(All)", ""))
            for pri in self._get_priorities_db():
                self.priorities.append((pri.priority, '%d - %s' %
                    (pri.priority, pri.keyword), pri.description))
        return self.priorities

    def get_legal_priorities(self):
        """
        Build up a table that can be used to verify the priority-parameter.
        """
        if not self.legal_priorities:
            self.legal_priorities = []
            for pri in self._get_priorities_db():
                self.legal_priorities.append(pri.priority)
        return self.legal_priorities

    def get_origins(self):
        """
        Prepare all origins for display in web-page.
        """
        if not self.origins:
            self.origins = []
            self.origins.append((0, '(All)'))
            for orig in self._get_origins_db():
                shortorigin = orig.name
                for domain_suffix in self.DOMAIN_SUFFICES:
                    shortorigin = re.sub(domain_suffix, '', shortorigin)
                self.origins.append((orig.origin, shortorigin))
        return self.origins

    def get_originid2origin(self):
        """
        Map an origin-identity to an origin-name.
        """
        if not self.originid2origin:
            self.originid2origin = {}
            for origin in self._get_origins_db():
                shortorigin = origin.name
                for domain_suffix in self.DOMAIN_SUFFICES:
                    shortorigin = re.sub(domain_suffix, '', shortorigin)
                self.originid2origin[origin.origin] = shortorigin
        return self.originid2origin

    def get_origin2originid(self):
        """
        Map an origin-name to an origin-identity.
        """
        if not self.origin2originid:
            self.origin2originid = {}
            for origin in self._get_origins_db():
                shortorigin = origin.name
                self.origin2originid[shortorigin] = origin.origin
                for domain_suffix in self.DOMAIN_SUFFICES:
                    shortorigin = re.sub(domain_suffix, '', shortorigin)
                self.origin2originid[shortorigin] = origin.origin
        return self.origin2originid

    def get_types(self):
        """
        Prepare all message-types for display in web-page.
        """
        if not self.types:
            self.types = []
            self.types.append((0, '(All)'))
            for mess_type in self._get_message_types_db():
                the_type = '%s-%d-%s' % (mess_type.facility,
                                 mess_type.priority.priority,
                                 mess_type.mnemonic)
                self.types.append((mess_type.type, the_type))
        return self.types

    def get_type2typeid(self):
        """
        Map a type-name to a type-identity.
        """
        if not self.type2typeid:
            self.type2typeid = {}
            for mess_type in self._get_message_types_db():
                the_type = '%s-%d-%s' % (mess_type.facility,
                                 mess_type.priority.priority,
                                 mess_type.mnemonic)
                self.type2typeid[the_type] = mess_type.type
        return self.type2typeid

    def get_typeid2type(self):
        """
        Map a type-identity to a type-name.
        """
        if not self.typeid2type:
            self.typeid2type = {}
            for mess_type in self._get_message_types_db():
                the_type = '%s-%d-%s' % (mess_type.facility,
                                 mess_type.priority.priority,
                                 mess_type.mnemonic)
                self.typeid2type[mess_type.type] = the_type
        return self.typeid2type


class ParamUtil(object):
    """
    A utillity-class that handles GET-parameters in the URL.
    Get the parameters and check for validity before returning values.
    """
    logger = logging.getLogger("nav.web.loggerhandler.utils.ParamUtil")

    DATEFORMAT = "%Y-%m-%d %H:%M:%S"
    DATE_REGEXP = re.compile('^\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2}$')

    def __init__(self, request, db_access):
        """
        Good old constructor...
        """
        super(ParamUtil, self).__init__()
        self.request = request
        self.db_access = db_access
        self.time_to_param = None
        self.time_from_param = None
        self.priority_param = None
        self.type_param = None
        self.origin_param = None
        self.category_param = None

    def _get_named_param(self, param_name):
        """
        Check for the presens of a given parameter in the request-object.
        Return the value of the parameter if found.
        """
        param = None
        if (param_name in self.request.GET
                and self.request.GET.get(param_name, None)):
            param = self.request.GET.get(param_name, None)
        return param

    def get_time_to(self):
        """
        Return the value of the the 'tto' parameter if it exist; otherwise
        return None.
        """
        if not self.time_to_param:
            tto = self._get_named_param('tto')
            if tto:
                if self.DATE_REGEXP.match(tto):
                    self.time_to_param = tto
        else:
            self.time_to_param = datetime.datetime.now().strftime(
                                                        self.DATEFORMAT)
        return self.time_to_param

    def get_time_from(self):
        """
        Return the value of the the 'tfrom' parameter if it exist; otherwise
        return None.
        """
        if not self.time_from_param:
            tfrom = self._get_named_param('tfrom')
            if tfrom:
                if self.DATE_REGEXP.match(tfrom):
                    self.time_from_param = tfrom
            else:
                tfrom = datetime.datetime.now() - datetime.timedelta(days=1)
                self.time_from_param = tfrom.strftime(self.DATEFORMAT)
        return self.time_from_param

    def get_priority(self):
        """
        Return the value of the the 'priority' parameter if it exist and
        is different from '-'; otherwise return None.
        """
        if not self.priority_param:
            pri = self._get_named_param('priority')
            if pri and pri != '-':
                if pri.isdigit():
                    pri = int(pri)
                    if pri in self.db_access.get_legal_priorities():
                        self.priority_param = pri
        return self.priority_param

    def get_type(self):
        """
        Return the value of the the 'type' parameter if it exist; otherwise
        return None.
        """
        if not self.type_param:
            the_type = self._get_named_param('type')
            if the_type:
                if the_type in self.db_access.get_type2typeid():
                    self.type_param = the_type
        return self.type_param

    def get_origin(self):
        """
        Return the value of the the 'origin' parameter if it exist; otherwise
        return None.
        """
        if not self.origin_param:
            orig = self._get_named_param('origin')
            if orig:
                if orig in self.db_access.get_origin2originid():
                    self.origin_param = orig
        return self.origin_param

    def get_category(self):
        """
        Return the value of the the 'category' parameter if it exist; otherwise
        return None.
        """
        if not self.category_param:
            cat = self._get_named_param('category')
            if (cat) in self.db_access.get_categories():
                self.category_param = cat
        return self.category_param
