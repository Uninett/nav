# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""
Forward alerts from Whatsup.

This just forwards the message directly using two variables: $subject
and $body. The formatting of the message is done in WhatsUp.
"""

import nav.mailin


class Plugin(nav.mailin.Plugin):
    def init(self):
        nav.event.create_type_hierarchy(
            {('whatsup', 'Alert from WhatsUp', False):
                 [('whatsup', 'Alert from WhatUp')]})

    def accept(self, msg):
        return msg['From'] == '<ita_wu@asp.uit.no>'

    def authorize(self, msg):
        return msg['Received'].endswith('.uit.no')

    def process(self, msg):
        body = msg.get_payload()
        body = body.decode('iso-8859-1').encode('utf-8')  # Temporary fix

        event = nav.mailin.make_event(eventtypeid='mailinWhatsup')
        event['subject'] = msg['Subject']
        event['body'] = body

        return event
