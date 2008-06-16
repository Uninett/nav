#! /usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2006 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Package placeholder. If you remove it, the package won't work.
"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"
__id__ = "$Id$"

import logging

from django.db.models import Q

from nav.models.profiles import Account, AccountAlertQueue, FilterGroup
from nav.models.event import AlertQueue

logging.basicConfig(level=logging.DEBUG)

# Build a mapping from db_tables to django models, and from db_columns to
# attributes. This code relies on the internal model attribute _meta which
# contains information about among other things db_tabels and db_columns
_mapping = {}
for model in [AccountAlertQueue]:
    _mapping[model._meta.db_table] = (model, dict([(f.db_column or f.attname, f.attname) for f in model._meta.fields]))

def check_alerts():
    new_alerts = AlertQueue.objects.new_alerts()

    # Get all users with an active profile
    for account in Account.objects.filter(alertpreference__active_profile__isnull=False):
            logging.debug("Cheking alerts for account '%s'" % account)

            permision_check = Q(group_permisions__account=account)
            in_profile_check = Q(alertsubscription__in=account.get_active_profile().get_active_timeperiod().alertsubscription_set.all())

            filter_groups = FilterGroup.objects.filter()

            for filter_group in filter_groups:
                logging.debug("Checking equipment group '%s' (%s)" % (filter_group, account))

                for content in filter_group.filtergroupcontent_set.all():
                    logging.debug("Checking filter '%s' in group '%s' (%s)" % (content, filter_group, account))

                    for expresion in content.filter.expresion_set.all():
                        logging.debug("Cheking if '%s' %s '%s'" % (expresion.match_field, expresion.get_match_type_display(), expresion.value))

                        print '%s%s' % (expresion.match_field.get_lookup_mapping, expresion.operator.get_operator_mapping)

    return new_alerts
