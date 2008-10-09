# -*- coding: ISO8859-1 -*-
#
# Copyright 2003 Norwegian University of Science and Technology
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
# Authors: Stian Søiland <stain@itea.ntnu.no>
#
"""
Exceptions and errors related to NAV.
"""


class GeneralException(Exception):
    "General exception"
    # Just subclass this with a new doc-string
    def __str__(self):
        # Returns a nice version of the docstring
        args = Exception.__str__(self) # Get our arguments
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
