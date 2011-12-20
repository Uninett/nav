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
"""macwatch view definitions"""

import logging
import os
#import datetime
from ConfigParser import ConfigParser

from django.http import HttpResponseRedirect
from django.template import RequestContext
#from django.template import Context
from django.shortcuts import render_to_response

import nav

from nav.django.utils import get_account

#from nav.models.logger import LoggerCategory
#from nav.models.logger import Origin
#from nav.models.logger import Priority
#from nav.models.logger import LogMessageType
#from nav.models.logger import LogMessage
from nav.models.logger import ErrorError
#from nav.models.logger import MessageView

from nav.web.loggerhandler.utils import DbAccess
from nav.web.loggerhandler.utils import ParamUtil


NAVBAR = [('Home', '/'), ('Syslog Analyzer', None)]
DEFAULT_VALUES = {'title': "Syslog Analyzer", 'navpath': NAVBAR}

logger = logging.getLogger("nav.web.loggerhandler")


def _get_basic_info_dict(db_access, param_util):
    """
    Get all default parameters for view.
    """
    origin_param = param_util.get_origin()
    type_param = param_util.get_type()
    link = []
    error_list = []
    info_dict = {'priority': param_util.get_priority(),
                 'origin': origin_param,
                 'originid': db_access.get_origin2originid().get(origin_param,
                                                                None),
                 'category': param_util.get_category(),
                 'type': type_param,
                 'typeid': db_access.get_type2typeid().get(type_param, None),
                 'tto': param_util.get_time_to(),
                 'tfrom': param_util.get_time_from(),
                 'priorities': db_access.get_priorities(),
                 'types': db_access.get_types(),
                 'categories': db_access.get_categories(),
                 'origins': db_access.get_origins(),
                 'origindict':  db_access.get_originid2origin(),
                 'typedict': db_access.get_typeid2type(),
                 'link': link,
                 'error_list': error_list,
                 }
    info_dict.update(DEFAULT_VALUES)
    return info_dict


def index(request):
    """
    Default handler.
    """
    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    db_access = DbAccess()
    param_util = ParamUtil(request, db_access)
    info_dict = _get_basic_info_dict(db_access, param_util)
    return render_to_response('loggerhandler/index.html',
                                info_dict,
                                RequestContext(request))


def exceptions(request):
    """
    Handler for exception-mode.
    """
    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    db_access = DbAccess()
    param_util = ParamUtil(request, db_access)
    info_dict = _get_basic_info_dict(db_access, param_util)
    config = ConfigParser()
    config.read(os.path.join(nav.path.sysconfdir, 'logger.conf'))
    options = config.options("priorityexceptions")
    excepts = []
    for option in options:
        newpriority = config.get("priorityexceptions", option)
        excepts.append((option, newpriority))
    info_dict['exceptions'] = excepts
    info_dict['exceptions_mode'] = True
    return render_to_response('loggerhandler/index.html',
                                info_dict,
                                RequestContext(request))


def errors(request):
    """
    Handler for error-mode.
    """
    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    db_access = DbAccess()
    param_util = ParamUtil(request, db_access)
    info_dict = _get_basic_info_dict(db_access, param_util)
    errs = []
    for err in ErrorError.objects.all():
        errs.append(err.message)
    info_dict['errors'] = errs
    info_dict['errors_count'] = len(errs)
    info_dict['errors_mode'] = True
    return render_to_response('loggerhandler/index.html',
                                info_dict,
                                RequestContext(request))
