"""
$Id$

This file is part of the NAV project.

Exceptions and errors related to NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Stian Søiland <stain@itea.ntnu.no>
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
        return args    

class ConfigurationError(GeneralException):
    "Configuration error"

class BasepathError(ConfigurationError):
    "Configuration error, unknown basepath"

class RedirectError(GeneralException):
    "Need to redirect"
    # raise with URL, dispatcher.py will redirect

class NoServicesFound(GeneralException):
    "No services found for device"
