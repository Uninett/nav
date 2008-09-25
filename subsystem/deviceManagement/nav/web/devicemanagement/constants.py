# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2007 UNINETT AS
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
#
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#
"""
Constants for Device Managment modules
"""

### Imports

import mx.DateTime

### Constants
# Should be read from config file

BASEPATH = '/devicemanagement/'
DATEFORMAT = '%Y-%m-%d'
TIMEFORMAT = '%Y-%m-%d %H:%M'
TIMESTAMP = '%Y-%m-%d %H:%M:%S'
INFINITY = mx.DateTime.DateTime(999999,12,31,0,0,0)
MAX_NUMBER_OF_DEVICES_ORDERED = 20
NUMBER_OF_ARRIVED_SERIALS = 10
DELETE_TIME_THRESHOLD = mx.DateTime.TimeDelta(hours=48)

MAIN_MENU = [['Device history',BASEPATH,'Browse and view device history'],
             ['Order devices',BASEPATH + 'order/','Order new devices and register arrivals of devices with serials'],
             ['Register serial numbers',BASEPATH + 'register/','Register new devices with serials'],
             ['Register RMA',BASEPATH + 'rma/','Register a RMA request'],
             ['Register error event',BASEPATH + 'error/','Register an error event with a comment on a location, room, box or module'],
             ['Module delete',BASEPATH + 'delete/','Manually delete any modules that are flagged as down']]

CURRENT_PATH = [('Home', '/'),
                ('Device Management', BASEPATH)]

# Controlnames for TreeSelect
CN_LOCATION = 'location'
CN_ROOM = 'room'
CN_BOX = 'netbox'
CN_MODULE = 'module'
CN_DEVICE = 'device'

# RMA module
CN_ADD_DEVICE = 'r_dadd'
CN_ADD_RMA = 'r_radd'
CN_RMANUMBER = 'r_number'
CN_RMACOMMENT = 'r_comment'
CN_RMARETAILER = 'r_retailer'
CN_ADDED_DEVICES = 'r_added'

# Error module
CN_ERRCOMMENT = 'e_comment'

# Order module
CN_YEAR = 'o_year'
CN_MONTH = 'o_month'
CN_DAY = 'o_day'
CN_RETAILER = 'o_retailer'
CN_COMMENT = 'o_comment'
CN_ORDERNUMBER = 'o_ordernumber'
CN_PRODUCT = 'o_product'
CN_AMOUNT = 'o_amount'
CN_ADD_SUBMIT = 'o_asubmit'
CN_ADD_CONFIRM = 'o_confirm'
CN_UPDATE_SUBMIT = 'o_usubmit'
CN_UPDATE_CONFIRM = 'o_uconfirm'
CN_CANCEL = 'o_cancel'
CN_ORG = 'o_org'
CN_DELETE_CONFIRM = 'o_dconfirm'
CN_ARRIVE_CONFIRM = 'o_arsubmit'
CN_STATE = 'o_action'
CN_SERIAL = 'o_serial'
CN_PENDING = 'o_pending'
CN_ARRIVED = 'o_arrived'
CN_CANCELLED = 'o_cancelled'

# Delete module
CN_DELETE_MODULE = 'd_delete'
CN_DELETE_MODULE_CONFIRM = 'd_confirm'
CN_MODULE_SELECT = 'd_moduleid'
CN_MOVETO = 'd_moveto'
CN_INVENTORY_MOVE = 'd_imoveto'
CN_INACTIVE_MOVE = 'd_inmoveto'

## History
# Global
G_EVENTTYPE = '%et%'
G_ALERTTYPE = '%at%'
G_ALLVARS = '%av%'
G_ALLMSGS = '%am%'

# deviceActive
# deviceState
# deviceNotice
DN_E_USERNAME = '$dn_e_u$'
DN_E_COMMENT = '$dn_e_c$'
DN_E_UNITTYPE = '$dn_e_ut$'
DN_E_LOCATIONID = '$dn_e_l$'
DN_E_ROOMID = '$dn_e_r$'
