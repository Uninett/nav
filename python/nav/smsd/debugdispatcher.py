# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A dispatcher for debugging the SMSd daemon.

This dispatcher WILL NOT send any SMS messages, it will only log them.
The dispatcher can be configured to report success or failure to the
daemon, in order to test various aspects of the SMS daemon.

"""

import logging
from nav.smsd.dispatcher import (Dispatcher, DispatcherError,
                                 PermanentDispatcherError)

_logger = logging.getLogger(__name__)


class DebugDispatcher(Dispatcher):
    """Debug dispatcher for smsd."""
    RESULT_PERMANENT = 'permanent'
    RESULT_FAIL = 'fail'
    RESULT_SUCCESS = 'success'
    RESULT_ERROR = 'error'

    OPTIONS = [RESULT_PERMANENT, RESULT_FAIL, RESULT_SUCCESS, RESULT_ERROR]

    def __init__(self, config):
        # Call mother's init
        Dispatcher.__init__(self)

        # Get config
        try:
            # Result of "dispatch" attempts
            self.result = config['result']
        except KeyError as error:
            raise DispatcherError("Config option not found: %s" % error)

        if self.result.lower() not in self.OPTIONS:
            raise DispatcherError("Invalid value %r for option 'result'. "
                                  "Must be one of: " + ", ".join(self.OPTIONS),
                                  self.result)
        else:
            self.result = self.result.lower()

    def sendsms(self, phone, msgs):
        """Log SMS message and report pre-configured result."""

        # Format SMS
        (sms, sent_count, ignored_count) = self.formatsms(msgs)
        _logger.info("SMS to %s: %s", phone, sms)
        smsid = 0
        result = True

        if self.result == self.RESULT_FAIL:
            result = False
            _logger.info("Returning failed status")
        if self.result == self.RESULT_SUCCESS:
            _logger.info("Returning success status")
        elif self.result == self.RESULT_ERROR:
            _logger.info("Raising DispatcherError")
            raise DispatcherError("Failed, because I was configured to.")
        elif self.result == self.RESULT_PERMANENT:
            _logger.info("Raising PermanentDispatcherError")
            raise PermanentDispatcherError(
                "Failed permanently, because I was configured to.")

        return (sms, sent_count, ignored_count, result, smsid)
