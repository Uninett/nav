#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Exceptions and errors related to NAV."""


class GeneralException(Exception):
    "General exception"

    # Just subclass this with a new doc-string
    def __str__(self):
        # Returns a nice version of the docstring
        args = Exception.__str__(self)  # Get our arguments
        result = self.__doc__
        if args:
            result += ": %s" % args
        return result


class ConfigurationError(GeneralException):
    "Configuration error"


class BasepathError(ConfigurationError):
    "Configuration error, unknown basepath"


class RedirectError(GeneralException):
    "Need to redirect"

    # raise with URL, dispatcher.py will redirect


class NoServicesFound(GeneralException):
    "No services found for netbox"


class NoNetboxTypeError(GeneralException):
    "This netbox has no type"
